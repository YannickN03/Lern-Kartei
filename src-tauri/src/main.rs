// Desktop-Einstieg (Android nutzt `lib.rs` → mobile_entry_point).
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    lernkartei_lib::run()
}
