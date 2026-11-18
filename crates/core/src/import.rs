//! Import aus JSON, CSV/TSV, Markdown und Text. Ergebnis: Decks ohne IDs (vergibt `store`).
//!
//! Unterstützt:
//! * JSON: Deck `{name, category, cards:[{front, back, tags}]}`, Liste von Decks,
//!   Bibliothek `{decks:[…]}` oder reine Kartenliste `[{front, back}]` (Aliase: q/a, frage/antwort).
//! * CSV/TSV: `Vorderseite;Rückseite;Tags` (Trenner `;` `,` Tab automatisch, Tags mit `|`).
//! * Text/Markdown: `Frage :: Antwort` je Zeile, `F:`/`A:`-Blöcke oder `## Frage` + Text als Antwort.
use crate::model::{Card, Deck};
use serde_json::Value;

#[derive(Debug, PartialEq)]
pub enum ImportError {
    Empty,
    Json(String),
}

impl std::fmt::Display for ImportError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ImportError::Empty => write!(f, "Keine Karten gefunden"),
            ImportError::Json(e) => write!(f, "Ungültiges JSON: {e}"),
        }
    }
}

/// Erkennt das Format anhand Dateiname und Inhalt.
pub fn parse(
    file_name: &str,
    content: &str,
    fallback_name: &str,
) -> Result<Vec<Deck>, ImportError> {
    let content = content.trim_start_matches('\u{feff}');
    let lower = file_name.to_lowercase();
    let trimmed = content.trim_start();
    let decks = if lower.ends_with(".json") || trimmed.starts_with('{') || trimmed.starts_with('[')
    {
        parse_json(content, fallback_name)?
    } else if lower.ends_with(".csv") || lower.ends_with(".tsv") {
        vec![deck(fallback_name, parse_csv(content))]
    } else {
        vec![deck(fallback_name, parse_text(content))]
    };
    let decks: Vec<Deck> = decks.into_iter().filter(|d| !d.cards.is_empty()).collect();
    if decks.is_empty() {
        return Err(ImportError::Empty);
    }
    Ok(decks)
}

fn deck(name: &str, cards: Vec<Card>) -> Deck {
    Deck {
        name: name.to_string(),
        cards,
        ..Default::default()
    }
}

pub fn parse_json(content: &str, fallback_name: &str) -> Result<Vec<Deck>, ImportError> {
    let v: Value = serde_json::from_str(content).map_err(|e| ImportError::Json(e.to_string()))?;
    let decks = match v {
        Value::Object(ref o) if o.contains_key("decks") => {
            from_list(o["decks"].clone(), fallback_name)?
        }
        Value::Object(ref o) if o.contains_key("cards") => vec![to_deck(v.clone(), fallback_name)?],
        Value::Object(_) => vec![deck(fallback_name, vec![to_card(v)?])],
        Value::Array(ref items) if items.iter().any(|i| i.get("cards").is_some()) => {
            from_list(v, fallback_name)?
        }
        Value::Array(items) => vec![deck(
            fallback_name,
            items.into_iter().map(to_card).collect::<Result<_, _>>()?,
        )],
        _ => return Err(ImportError::Empty),
    };
    Ok(decks
        .into_iter()
        .map(|mut d| {
            d.cards.retain(|c| !c.front.trim().is_empty());
            d
        })
        .collect())
}

fn from_list(v: Value, fallback: &str) -> Result<Vec<Deck>, ImportError> {
    match v {
        Value::Array(items) => items.into_iter().map(|i| to_deck(i, fallback)).collect(),
        _ => Err(ImportError::Empty),
    }
}

fn to_deck(v: Value, fallback: &str) -> Result<Deck, ImportError> {
    let mut d: Deck = serde_json::from_value(v).map_err(|e| ImportError::Json(e.to_string()))?;
    if d.name.trim().is_empty() {
        d.name = fallback.to_string();
    }
    Ok(d)
}

fn to_card(v: Value) -> Result<Card, ImportError> {
    serde_json::from_value(v).map_err(|e| ImportError::Json(e.to_string()))
}

/// CSV mit Anführungszeichen-Unterstützung; erste Zeile wird als Kopf erkannt und übersprungen.
pub fn parse_csv(content: &str) -> Vec<Card> {
    let first = content.lines().next().unwrap_or("");
    let delim = [
        ('\t', first.matches('\t').count()),
        (';', first.matches(';').count()),
        (',', first.matches(',').count()),
    ]
    .into_iter()
    .max_by_key(|(_, n)| *n)
    .map(|(c, _)| c)
    .unwrap_or(';');
    let rows = csv_rows(content, delim);
    let mut cards = Vec::new();
    for (i, row) in rows.iter().enumerate() {
        if row.len() < 2 || row[0].trim().is_empty() {
            continue;
        }
        let head = row[0].trim().to_lowercase();
        if i == 0 && ["front", "vorderseite", "frage", "question", "q"].contains(&head.as_str()) {
            continue;
        }
        let tags = row
            .get(2)
            .map(|t| {
                t.split(['|', ','])
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
                    .collect()
            })
            .unwrap_or_default();
        cards.push(Card {
            front: row[0].trim().into(),
            back: row[1].trim().into(),
            tags,
            ..Default::default()
        });
    }
    cards
}

fn csv_rows(s: &str, delim: char) -> Vec<Vec<String>> {
    let mut rows = vec![];
    let mut row = vec![];
    let mut field = String::new();
    let mut quoted = false;
    let mut chars = s.chars().peekable();
    while let Some(c) = chars.next() {
        match c {
            '"' if quoted && chars.peek() == Some(&'"') => {
                field.push('"');
                chars.next();
            }
            '"' if quoted => quoted = false,
            '"' if field.is_empty() => quoted = true,
            c if c == delim && !quoted => row.push(std::mem::take(&mut field)),
            '\r' if !quoted => {}
            '\n' if !quoted => {
                row.push(std::mem::take(&mut field));
                rows.push(std::mem::take(&mut row));
            }
            c => field.push(c),
        }
    }
    if !field.is_empty() || !row.is_empty() {
        row.push(field);
        rows.push(row);
    }
    rows
}

/// Text/Markdown-Import.
pub fn parse_text(content: &str) -> Vec<Card> {
    let content = content.replace("\r\n", "\n");
    // 1) Zeilen mit „ :: “
    if content.lines().filter(|l| l.contains(" :: ")).count() >= 1
        && !content.contains("\n## ")
        && !content.starts_with("## ")
    {
        return content
            .lines()
            .filter_map(|l| l.split_once(" :: "))
            .map(|(f, b)| Card {
                front: f.trim().into(),
                back: b.replace("\\n", "\n").trim().into(),
                ..Default::default()
            })
            .filter(|c| !c.front.is_empty())
            .collect();
    }
    // 2) Markdown-Überschriften: „## Frage“ → folgender Text ist Antwort
    if content
        .lines()
        .any(|l| l.starts_with("## ") || l.starts_with("### "))
    {
        let mut cards = vec![];
        let mut cur: Option<Card> = None;
        for line in content.lines() {
            if let Some(h) = line
                .strip_prefix("### ")
                .or_else(|| line.strip_prefix("## "))
            {
                if let Some(c) = cur.take() {
                    cards.push(c);
                }
                cur = Some(Card {
                    front: h.trim().into(),
                    ..Default::default()
                });
            } else if let Some(c) = cur.as_mut() {
                c.back.push_str(line);
                c.back.push('\n');
            }
        }
        cards.extend(cur);
        for c in &mut cards {
            c.back = c.back.trim().to_string();
        }
        return cards;
    }
    // 3) F:/A:-Blöcke
    let mut cards = vec![];
    let mut cur = Card::default();
    let mut in_back = false;
    let flush = |cur: &mut Card, cards: &mut Vec<Card>| {
        if !cur.front.trim().is_empty() {
            let mut c = std::mem::take(cur);
            c.front = c.front.trim().into();
            c.back = c.back.trim().into();
            cards.push(c);
        }
        *cur = Card::default();
    };
    for line in content.lines() {
        let l = line.trim_start();
        let q = ["F:", "Q:", "Frage:"]
            .iter()
            .find_map(|p| l.strip_prefix(p));
        let a = ["A:", "Antwort:"].iter().find_map(|p| l.strip_prefix(p));
        if let Some(q) = q {
            flush(&mut cur, &mut cards);
            cur.front = q.trim().into();
            in_back = false;
        } else if let Some(a) = a {
            cur.back = a.trim().into();
            in_back = true;
        } else if l.is_empty() && in_back {
            cur.back.push('\n');
        } else if in_back {
            cur.back.push('\n');
            cur.back.push_str(line);
        } else if !cur.front.is_empty() {
            cur.front.push('\n');
            cur.front.push_str(line);
        }
    }
    flush(&mut cur, &mut cards);
    cards
}
