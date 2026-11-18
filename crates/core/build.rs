//! Bettet alle Decks aus `content/decks/*.json` ein. Neues Deck = Datei ablegen, fertig.
//! Außerdem: Shorts-Manifest `content/shorts.json` + Liste der Videodateien in `ui/shorts/`.
use std::{env, fs, path::Path};

const VIDEO_EXT: &[&str] = &["mp4", "m4v", "webm"];

fn main() {
    let manifest = env::var("CARGO_MANIFEST_DIR").unwrap();
    let root = Path::new(&manifest).join("../..");
    let dir = root.join("content/decks");
    println!("cargo:rerun-if-changed={}", dir.display());
    let mut files: Vec<_> = fs::read_dir(&dir)
        .map(|rd| rd.filter_map(|e| e.ok().map(|e| e.path())).collect())
        .unwrap_or_default();
    files.retain(|p| p.extension().is_some_and(|e| e == "json"));
    files.sort();
    let mut out = String::from("pub static BUILTIN_DECKS: &[(&str, &str)] = &[\n");
    for f in &files {
        println!("cargo:rerun-if-changed={}", f.display());
        let abs = fs::canonicalize(f).unwrap();
        let name = f.file_name().unwrap().to_string_lossy();
        out.push_str(&format!(
            "    ({name:?}, include_str!({:?})),\n",
            abs.display().to_string()
        ));
    }
    out.push_str("];\n");

    // Shorts: Manifest (optional) + vorhandene Videodateien
    let sm = root.join("content/shorts.json");
    println!("cargo:rerun-if-changed={}", sm.display());
    match fs::canonicalize(&sm) {
        Ok(abs) => out.push_str(&format!(
            "pub static SHORTS_MANIFEST: &str = include_str!({:?});\n",
            abs.display().to_string()
        )),
        Err(_) => out.push_str("pub static SHORTS_MANIFEST: &str = \"\";\n"),
    }
    let vdir = root.join("ui/shorts");
    println!("cargo:rerun-if-changed={}", vdir.display());
    let mut videos: Vec<String> = fs::read_dir(&vdir)
        .map(|rd| {
            rd.filter_map(|e| e.ok())
                .filter(|e| {
                    e.path()
                        .extension()
                        .and_then(|x| x.to_str())
                        .is_some_and(|x| VIDEO_EXT.contains(&x.to_lowercase().as_str()))
                })
                .map(|e| e.file_name().to_string_lossy().into_owned())
                .collect()
        })
        .unwrap_or_default();
    videos.sort();
    out.push_str(&format!("pub static SHORT_FILES: &[&str] = &{videos:?};\n"));

    fs::write(
        Path::new(&env::var("OUT_DIR").unwrap()).join("builtin.rs"),
        out,
    )
    .unwrap();
}
