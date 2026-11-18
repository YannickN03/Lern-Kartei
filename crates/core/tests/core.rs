use lernkartei_core::{import, schedule, store, Library, Rating};
use std::collections::HashSet;

const NOW: i64 = 1_763_460_000; // 2025-11-18

#[test]
fn builtin_content_is_valid() {
    let decks = store::builtin_decks();
    assert!(decks.len() >= 10, "zu wenige Standard-Decks");
    let mut deck_ids = HashSet::new();
    for d in &decks {
        assert!(deck_ids.insert(d.id.clone()), "doppelte Deck-ID {}", d.id);
        assert!(
            !d.name.is_empty() && !d.category.is_empty(),
            "{}: Name/Kategorie fehlt",
            d.id
        );
        assert!(d.color.starts_with('#'), "{}: Farbe fehlt", d.id);
        assert!(!d.cards.is_empty(), "{}: keine Karten", d.id);
        let mut ids = HashSet::new();
        for c in &d.cards {
            assert!(
                ids.insert(c.id.clone()),
                "{}: doppelte Vorderseite: {}",
                d.id,
                c.front
            );
            assert!(
                !c.back.trim().is_empty(),
                "{}: leere Rückseite: {}",
                d.id,
                c.front
            );
            assert!(c.prio <= 5, "{}: prio>5", d.id);
            assert_eq!(
                c.front.matches("==").count() % 2,
                0,
                "{}: unpaariges == in {}",
                d.id,
                c.front
            );
            assert_eq!(
                c.back.matches("==").count() % 2,
                0,
                "{}: unpaariges == in {}",
                d.id,
                c.front
            );
            assert_eq!(
                c.back.matches("```").count() % 2,
                0,
                "{}: unpaariges ``` in {}",
                d.id,
                c.front
            );
        }
    }
}

#[test]
fn leitner_progression() {
    let mut p = Default::default();
    schedule::rate(&mut p, Rating::Kann, NOW);
    assert_eq!((p.leitner_box, p.due), (1, schedule::today(NOW) + 1));
    schedule::rate(&mut p, Rating::Kann, NOW);
    schedule::rate(&mut p, Rating::Kann, NOW);
    assert_eq!(p.leitner_box, 3);
    schedule::rate(&mut p, Rating::Geht, NOW);
    assert_eq!(p.leitner_box, 2);
    schedule::rate(&mut p, Rating::Nicht, NOW);
    assert_eq!((p.leitner_box, p.lapses, p.reviews), (0, 1, 5));
    for _ in 0..10 {
        schedule::rate(&mut p, Rating::Kann, NOW);
    }
    assert_eq!(p.leitner_box, schedule::MAX_BOX);
}

#[test]
fn merge_keeps_progress_and_edits() {
    let mut lib = Library::default();
    let r = store::merge_builtin(&mut lib, false);
    assert!(r.cards_added > 0);
    let (d, c) = (lib.decks[0].id.clone(), lib.decks[0].cards[0].id.clone());
    store::review(&mut lib, &d, &c, Rating::Kann, NOW).unwrap();
    let r2 = store::merge_builtin(&mut lib, false);
    assert_eq!(
        (r2.cards_added, r2.decks_added, r2.cards_removed),
        (0, 0, 0)
    );
    assert_eq!(lib.card_mut(&d, &c).unwrap().progress.rating, Rating::Kann);
    // gelöschtes Standard-Deck bleibt weg, bis wiederhergestellt
    store::delete_deck(&mut lib, &d);
    store::merge_builtin(&mut lib, false);
    assert!(lib.deck(&d).is_none());
    store::merge_builtin(&mut lib, true);
    assert!(lib.deck(&d).is_some());
}

#[test]
fn import_formats() {
    let json = r#"{"name":"Test","category":"X","cards":[{"front":"A","back":"B","tags":["t"]},{"q":"C","a":"D"}]}"#;
    let d = import::parse("x.json", json, "F").unwrap();
    assert_eq!(
        (
            d[0].name.as_str(),
            d[0].cards.len(),
            d[0].cards[1].back.as_str()
        ),
        ("Test", 2, "D")
    );

    let list = r#"[{"frage":"1+1","antwort":"2"}]"#;
    assert_eq!(
        import::parse("l.json", list, "Liste").unwrap()[0].name,
        "Liste"
    );

    let csv = "Vorderseite;Rückseite;Tags\n\"Was ist; ACID?\";\"Atomarität,\nKonsistenz\";db|sql\nOSI;7 Schichten;\n";
    let c = import::parse("k.csv", csv, "CSV").unwrap();
    assert_eq!(c[0].cards.len(), 2);
    assert_eq!(c[0].cards[0].front, "Was ist; ACID?");
    assert_eq!(c[0].cards[0].tags, vec!["db", "sql"]);

    let txt = "F: Was ist DNS?\nA: Namensauflösung\nmehrzeilig\n\nF: Port HTTPS?\nA: 443";
    let t = import::parse("n.txt", txt, "T").unwrap();
    assert_eq!(t[0].cards.len(), 2);
    assert_eq!(t[0].cards[0].back, "Namensauflösung\nmehrzeilig");

    let md = "# Titel\n## Was ist REST?\nArchitekturstil\n\n## HTTP 404?\nNot Found";
    assert_eq!(import::parse("n.md", md, "M").unwrap()[0].cards.len(), 2);

    let colons = "SSH :: Port 22\nDNS :: Port 53";
    assert_eq!(
        import::parse("p.txt", colons, "P").unwrap()[0].cards[1].back,
        "Port 53"
    );

    assert!(import::parse("e.txt", "", "E").is_err());
}

#[test]
fn import_and_queue_and_export_roundtrip() {
    let mut lib = Library::default();
    let decks = import::parse("a.txt", "A :: 1\nB :: 2\nC :: 3", "Eigen").unwrap();
    assert_eq!(
        store::add_imported(&mut lib, decks, None, "", NOW).unwrap(),
        3
    );
    let id = lib.decks[0].id.clone();
    assert_eq!(lib.decks[0].category, "Eigene Karten");
    let q = schedule::queue(
        &lib,
        std::slice::from_ref(&id),
        schedule::Mode::Due,
        0,
        None,
        NOW,
    );
    assert_eq!(q.len(), 3);
    store::review(&mut lib, &id, &q[0].card.id, Rating::Kann, NOW).unwrap();
    store::review(&mut lib, &id, &q[1].card.id, Rating::Nicht, NOW).unwrap();
    assert_eq!(
        schedule::queue(&lib, &[], schedule::Mode::Due, 0, None, NOW).len(),
        2
    );
    assert_eq!(
        schedule::queue(&lib, &[], schedule::Mode::Weak, 0, None, NOW).len(),
        1
    );
    assert_eq!(
        schedule::queue(&lib, &[], schedule::Mode::All, 0, Some(42), NOW).len(),
        3
    );
    let ov = store::overview(&lib, NOW);
    assert_eq!(
        (ov.totals.kann, ov.totals.nicht, ov.totals.new, ov.streak),
        (1, 1, 1, 1)
    );

    let exported = store::export(&lib, &[], true);
    let back = import::parse("e.json", &exported, "x").unwrap();
    assert_eq!(back[0].cards.len(), 3);

    let dir = std::env::temp_dir().join(format!("lk-test-{}", std::process::id()));
    let path = dir.join("library.json");
    store::save(&path, &lib).unwrap();
    assert_eq!(store::load(&path).unwrap(), lib);
    std::fs::remove_dir_all(dir).ok();
}

#[test]
fn edit_card_marks_builtin_as_edited() {
    let mut lib = Library::default();
    store::merge_builtin(&mut lib, false);
    let d = lib.decks[0].id.clone();
    let c = lib.decks[0].cards[0].clone();
    let inp = store::CardInput {
        id: Some(c.id.clone()),
        front: c.front.clone(),
        back: "Neu".into(),
        ..Default::default()
    };
    store::upsert_card(&mut lib, &d, inp, NOW).unwrap();
    store::merge_builtin(&mut lib, false);
    assert_eq!(lib.card_mut(&d, &c.id).unwrap().back, "Neu");
    assert!(!store::search(&lib, "neu", 10).is_empty());
}

// ---------- Shorts ----------
use lernkartei_core::shorts::{self, Filter};

const MANIFEST: &str = r#"{"shorts":[
  {"file":"01-sql.mp4","title":"SQL","deck":"sql","tags":["SQL"]},
  {"file":"02-uml.mp4","deck":"uml-bpmn"},
  {"file":"03-fehlt.mp4","title":"Kommt noch","deck":"sql"}
]}"#;

#[test]
fn shorts_manifest_is_valid() {
    let decks = store::builtin_decks();
    let cat = shorts::catalog();
    let mut ids = HashSet::new();
    for s in &cat {
        assert!(ids.insert(s.id.clone()), "doppelte Short-ID {}", s.id);
        assert!(!s.title.is_empty(), "{}: Titel fehlt", s.id);
        assert!(!s.file.is_empty(), "{}: Datei fehlt", s.id);
        assert!(
            s.deck.is_empty() || decks.iter().any(|d| d.id == s.deck),
            "{}: unbekanntes Deck {}",
            s.id,
            s.deck
        );
    }
}

#[test]
fn shorts_catalog_merges_manifest_and_files() {
    let cat =
        shorts::catalog_from(MANIFEST, &["01-sql.mp4", "02-UML.mp4", "07-mein_video.mp4"]).unwrap();
    let ids: Vec<_> = cat.iter().map(|s| (s.id.as_str(), s.available)).collect();
    assert_eq!(
        ids,
        [
            ("01-sql", true),
            ("02-uml", true),
            ("03-fehlt", false),
            ("07-mein-video", true)
        ]
    );
    assert_eq!(cat[1].title, "Uml");
    assert_eq!(cat[3].title, "Mein video");
    assert!(shorts::catalog_from("{kaputt", &[]).is_err());
    assert!(shorts::catalog_from("", &[]).unwrap().is_empty());
}

#[test]
fn shorts_feed_progress_and_filters() {
    let mut lib = Library::default();
    store::merge_builtin(&mut lib, false);
    let cat = shorts::catalog_from(MANIFEST, &["01-sql.mp4", "02-uml.mp4"]).unwrap();

    let f = shorts::feed(&lib, &cat, Filter::All, None, None);
    assert_eq!(
        (f.total, f.seen, f.items.len(), f.upcoming.len()),
        (2, 0, 2, 1)
    );
    assert_eq!(f.items[0].deck_name, "SQL");

    shorts::mark_seen(&mut lib, &cat, "01-sql", NOW).unwrap();
    assert!(shorts::mark_seen(&mut lib, &cat, "gibtsnicht", NOW).is_err());
    let f = shorts::feed(&lib, &cat, Filter::All, None, None);
    assert_eq!(f.seen, 1);
    assert_eq!(f.items[0].short.id, "02-uml", "ungesehene zuerst");
    assert_eq!(
        shorts::feed(&lib, &cat, Filter::New, None, None)
            .items
            .len(),
        1
    );

    assert!(shorts::toggle_like(&mut lib, &cat, "02-uml").unwrap());
    let liked = shorts::feed(&lib, &cat, Filter::Liked, None, None);
    assert_eq!(liked.items.len(), 1);
    assert!(liked.items[0].liked);

    let sql = shorts::feed(&lib, &cat, Filter::All, Some("sql"), Some(42));
    assert_eq!((sql.items.len(), sql.upcoming.len()), (1, 1));

    // Speichern/Laden behält den Zustand, alte Dateien ohne `shorts` laden weiter
    let json = serde_json::to_string(&lib).unwrap();
    let back: Library = serde_json::from_str(&json).unwrap();
    assert_eq!(back.shorts, lib.shorts);
    let old: Library = serde_json::from_str(r#"{"version":1,"decks":[]}"#).unwrap();
    assert!(old.shorts.is_empty());

    shorts::reset_seen(&mut lib);
    let f = shorts::feed(&lib, &cat, Filter::All, None, None);
    assert_eq!(f.seen, 0);
    assert!(f.items.iter().any(|i| i.liked), "Merkliste bleibt");
}
