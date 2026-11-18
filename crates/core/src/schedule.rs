//! Leitner-Planung mit drei Antworten: Nicht / Geht so / Kann ich.
//!
//! Fach 0 = sofort wiederholen; jedes „Kann ich“ schiebt eine Karte ein Fach weiter.
//! Intervalle (Tage) je Fach: 0, 1, 3, 7, 14, 30.
use crate::model::{Card, Deck, Library, Progress, Rating};
use serde::{Deserialize, Serialize};

pub const INTERVALS: [i64; 6] = [0, 1, 3, 7, 14, 30];
pub const MAX_BOX: u8 = 5;

pub fn today(unix_secs: i64) -> i64 {
    unix_secs.div_euclid(86_400)
}

/// Bewertet eine Karte und aktualisiert Fach + Fälligkeit.
pub fn rate(p: &mut Progress, r: Rating, now: i64) {
    let day = today(now);
    match r {
        Rating::New => {
            *p = Progress::default();
            return;
        }
        Rating::Nicht => {
            if p.leitner_box > 1 {
                p.lapses += 1;
            }
            p.leitner_box = 0;
            p.due = day;
        }
        Rating::Geht => {
            p.leitner_box = p.leitner_box.saturating_sub(1).max(1);
            p.due = day + 1;
        }
        Rating::Kann => {
            p.leitner_box = (p.leitner_box + 1).min(MAX_BOX);
            p.due = day + INTERVALS[p.leitner_box as usize];
        }
    }
    p.rating = r;
    p.reviews += 1;
    p.last = now;
}

/// Manuelles Einsortieren (ohne Wiederholungszählung), z. B. aus der Kartenliste.
pub fn sort_into(p: &mut Progress, r: Rating, now: i64) {
    let reviews = p.reviews;
    rate(p, r, now);
    p.reviews = reviews;
}

pub fn is_due(c: &Card, day: i64) -> bool {
    c.progress.rating == Rating::New || c.progress.due <= day
}

#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq, Default)]
#[serde(rename_all = "lowercase")]
pub enum Mode {
    /// Fällige + neue Karten.
    #[default]
    Due,
    All,
    /// Nur „Nicht“ und „Geht so“.
    Weak,
    New,
    Flagged,
    Nicht,
    Geht,
    Kann,
}

pub fn matches(c: &Card, mode: Mode, day: i64) -> bool {
    let r = c.progress.rating;
    match mode {
        Mode::Due => is_due(c, day),
        Mode::All => true,
        Mode::Weak => matches!(r, Rating::Nicht | Rating::Geht),
        Mode::New => r == Rating::New,
        Mode::Flagged => c.flagged,
        Mode::Nicht => r == Rating::Nicht,
        Mode::Geht => r == Rating::Geht,
        Mode::Kann => r == Rating::Kann,
    }
}

#[derive(Serialize, Clone, Debug, PartialEq)]
pub struct StudyCard {
    pub deck_id: String,
    pub deck_name: String,
    pub color: String,
    pub card: Card,
}

/// Lernstapel: fällige zuerst nach Fach/Fälligkeit, neue Karten nach Priorität.
pub fn queue(
    lib: &Library,
    decks: &[String],
    mode: Mode,
    limit: usize,
    shuffle_seed: Option<u64>,
    now: i64,
) -> Vec<StudyCard> {
    let day = today(now);
    let mut out: Vec<StudyCard> = lib
        .decks
        .iter()
        .filter(|d| decks.is_empty() || decks.contains(&d.id))
        .flat_map(|d| {
            d.cards
                .iter()
                .filter(move |c| matches(c, mode, day))
                .map(move |c| StudyCard {
                    deck_id: d.id.clone(),
                    deck_name: d.name.clone(),
                    color: d.color.clone(),
                    card: c.clone(),
                })
        })
        .collect();
    match shuffle_seed {
        Some(seed) => shuffle(&mut out, seed),
        None => out.sort_by_key(|s| {
            let p = &s.card.progress;
            let new = p.rating == Rating::New;
            (new, p.leitner_box, p.due, std::cmp::Reverse(s.card.prio))
        }),
    }
    if limit > 0 {
        out.truncate(limit);
    }
    out
}

pub(crate) fn shuffle<T>(v: &mut [T], seed: u64) {
    let mut x = seed | 1;
    for i in (1..v.len()).rev() {
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        v.swap(i, (x % (i as u64 + 1)) as usize);
    }
}

#[derive(Serialize, Clone, Debug, Default, PartialEq)]
pub struct Counts {
    pub total: usize,
    pub new: usize,
    pub nicht: usize,
    pub geht: usize,
    pub kann: usize,
    pub due: usize,
    pub flagged: usize,
}

impl Counts {
    pub fn of(d: &Deck, day: i64) -> Self {
        let mut c = Counts {
            total: d.cards.len(),
            ..Default::default()
        };
        for card in &d.cards {
            match card.progress.rating {
                Rating::New => c.new += 1,
                Rating::Nicht => c.nicht += 1,
                Rating::Geht => c.geht += 1,
                Rating::Kann => c.kann += 1,
            }
            c.due += is_due(card, day) as usize;
            c.flagged += card.flagged as usize;
        }
        c
    }
    pub fn add(&mut self, o: &Counts) {
        self.total += o.total;
        self.new += o.new;
        self.nicht += o.nicht;
        self.geht += o.geht;
        self.kann += o.kann;
        self.due += o.due;
        self.flagged += o.flagged;
    }
}
