//! Datenmodell. Alles ist serde-(de)serialisierbar; Felder mit `default` halten alte Dateien kompatibel.
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Einsortierung einer Karte: Neu → Nicht / Geht so / Kann ich.
#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq, Default, Hash)]
#[serde(rename_all = "lowercase")]
pub enum Rating {
    #[default]
    New,
    Nicht,
    Geht,
    Kann,
}

/// Lernfortschritt (Leitner-Fach 0..=5, `due` = Unix-Tag).
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct Progress {
    pub rating: Rating,
    #[serde(rename = "box")]
    pub leitner_box: u8,
    pub due: i64,
    pub reviews: u32,
    pub lapses: u32,
    pub last: i64,
}

/// Freihand-Strich; `pts` = flache Liste x,y normiert auf die Kartenbreite.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct Stroke {
    pub color: String,
    pub width: f32,
    pub pts: Vec<f32>,
}

/// Anmerkungen einer Kartenseite: Wort-Markierungen [Wortindex, Farbe] + Stiftstriche.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct Ink {
    pub marks: Vec<[u32; 2]>,
    pub strokes: Vec<Stroke>,
}

impl Ink {
    pub fn is_empty(&self) -> bool {
        self.marks.is_empty() && self.strokes.is_empty()
    }
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct Card {
    pub id: String,
    #[serde(
        alias = "q",
        alias = "question",
        alias = "frage",
        alias = "vorderseite"
    )]
    pub front: String,
    #[serde(alias = "a", alias = "answer", alias = "antwort", alias = "rueckseite")]
    pub back: String,
    pub tags: Vec<String>,
    /// 1 (niedrig) … 5 (essentiell); 0 = nicht gesetzt.
    pub prio: u8,
    /// Bild als data-URL (optional).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image: Option<String>,
    #[serde(skip_serializing_if = "Ink::is_empty")]
    pub ink_front: Ink,
    #[serde(skip_serializing_if = "Ink::is_empty")]
    pub ink_back: Ink,
    pub progress: Progress,
    pub flagged: bool,
    /// Stammt aus den mitgelieferten Inhalten.
    pub builtin: bool,
    /// Vom Nutzer verändert → Inhalts-Updates überschreiben die Karte nicht.
    pub edited: bool,
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct Deck {
    pub id: String,
    pub name: String,
    /// Lernkategorie (Gruppierung auf dem Startbildschirm).
    pub category: String,
    pub description: String,
    pub color: String,
    pub icon: String,
    pub builtin: bool,
    pub cards: Vec<Card>,
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct Settings {
    /// Gelöschte Standard-Decks (werden bei Updates nicht wieder angelegt).
    pub hidden_builtin: Vec<String>,
    pub daily_goal: u32,
    pub streak: u32,
    pub streak_day: i64,
    pub reviews_today: u32,
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct Library {
    pub version: u32,
    pub decks: Vec<Deck>,
    pub settings: Settings,
    /// Fortschritt der Lern-Shorts (Schlüssel = Short-ID).
    #[serde(skip_serializing_if = "BTreeMap::is_empty")]
    pub shorts: BTreeMap<String, ShortState>,
}

/// Was der Nutzer mit einem Short gemacht hat.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct ShortState {
    /// Mindestens einmal (fast) zu Ende geschaut.
    pub seen: bool,
    /// Gemerkt ❤️
    pub liked: bool,
    pub views: u32,
    /// Zuletzt geschaut (Unix-Sekunden).
    pub last: i64,
}

impl Library {
    pub const VERSION: u32 = 1;

    pub fn deck(&self, id: &str) -> Option<&Deck> {
        self.decks.iter().find(|d| d.id == id)
    }
    pub fn deck_mut(&mut self, id: &str) -> Option<&mut Deck> {
        self.decks.iter_mut().find(|d| d.id == id)
    }
    pub fn card_mut(&mut self, deck: &str, card: &str) -> Option<&mut Card> {
        self.deck_mut(deck)?.cards.iter_mut().find(|c| c.id == card)
    }
}

/// FNV-1a 64 → kurze, stabile IDs.
pub fn hash_id(prefix: &str, parts: &[&str]) -> String {
    let mut h: u64 = 0xcbf29ce484222325;
    for p in parts {
        for b in p.bytes().chain(std::iter::once(0x1f)) {
            h ^= b as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
    }
    format!("{prefix}{:012x}", h & 0xffff_ffff_ffff)
}

/// Slug für Deck-IDs („Datenbanken & SQL“ → „datenbanken-sql“).
pub fn slug(s: &str) -> String {
    let mut out = String::new();
    for ch in s.to_lowercase().chars() {
        let mapped = match ch {
            'ä' => "ae".into(),
            'ö' => "oe".into(),
            'ü' => "ue".into(),
            'ß' => "ss".into(),
            c if c.is_ascii_alphanumeric() => c.to_string(),
            _ => "-".into(),
        };
        out.push_str(&mapped);
    }
    let parts: Vec<&str> = out.split('-').filter(|p| !p.is_empty()).collect();
    let s = parts.join("-");
    if s.is_empty() {
        "deck".into()
    } else {
        s
    }
}
