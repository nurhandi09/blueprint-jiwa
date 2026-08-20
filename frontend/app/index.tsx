import { Ionicons } from "@expo/vector-icons";
import { useEffect, useState } from "react";
import { ActivityIndicator, Modal, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { storage } from "@/src/utils/storage";

const API = `${process.env.EXPO_PUBLIC_BACKEND_URL}/api`;
// Warm off-white surface + deep green typography preserved from previous approved design.
// Book-blue #58A4C5 replaces the previous coral accent everywhere.
const C = {
  paper: "#F6F0E7",
  deep: "#EAE0D2",
  ink: "#29302D",
  muted: "#5D6862",
  forest: "#23483C",
  accent: "#58A4C5",       // book blue
  accentDeep: "#3E7F9B",   // darker for CTA text contrast
  accentSoft: "#DDEAF0",
  white: "#FFFDF8",
};
type Lang = "id" | "en";
type City = { id: string; name: string; country: string; timezone: string };
type Blueprint = { name: string; type: string; authority: string; profile: string; strategy: string; city: City; birth_date: string; birth_time: string };

const text = {
  id: {
    name: "Nama",
    date: "Tanggal lahir",
    time: "Jam lahir",
    city: "Kota kelahiran",
    choose: "Pilih kota",
    search: "Cari kota di dunia...",
    submit: "HITUNG CETAK BIRU",
    title: "Kenali Cetak Birumu",
    intro: "Masukkan data lahirmu untuk menghitung Cetak Biru berdasarkan Human Design.",
    helper: "Format tanggal: DD-MM-YYYY",
    again: "Buat ulang",
    resultHeading: "CETAK BIRU KAMU",
  },
  en: {
    name: "Name",
    date: "Birth date",
    time: "Birth time",
    city: "Birth city",
    choose: "Choose a city",
    search: "Search cities worldwide...",
    submit: "CALCULATE BLUEPRINT",
    title: "Meet your Cetak Biru",
    intro: "Enter your birth data to calculate your Cetak Biru based on Human Design.",
    helper: "Date format: DD-MM-YYYY",
    again: "Start over",
    resultHeading: "YOUR CETAK BIRU",
  },
};

export default function Index() {
  const [lang, setLang] = useState<Lang>("id");
  const t = text[lang];
  const [name, setName] = useState("");
  const [date, setDate] = useState("01-01-1990");
  const [time, setTime] = useState("12:00");
  const [cities, setCities] = useState<City[]>([]);
  const [city, setCity] = useState<City | null>(null);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [picker, setPicker] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Blueprint | null>(null);

  useEffect(() => {
    fetch(`${API}/cities`).then(r => r.json()).then(setCities).catch(() => setError("Koneksi belum tersedia."));
    storage.getItem("cetakbiru-lang").then(v => v && setLang(v as Lang));
  }, []);

  useEffect(() => {
    if (!picker) return;
    const q = query.trim();
    const url = q.length === 0 ? `${API}/cities` : `${API}/cities?q=${encodeURIComponent(q)}&limit=30`;
    setSearching(true);
    const handle = setTimeout(() => {
      fetch(url).then(r => r.json()).then(list => { setCities(list); setSearching(false); }).catch(() => setSearching(false));
    }, 250);
    return () => clearTimeout(handle);
  }, [query, picker]);

  const toggle = () => { const next = lang === "id" ? "en" : "id"; setLang(next); storage.setItem("cetakbiru-lang", next); };

  const submit = async () => {
    if (!name.trim()) return setError(lang === "id" ? "Masukkan nama terlebih dahulu." : "Enter your name first.");
    if (!city) return setError(lang === "id" ? "Pilih kota terlebih dahulu." : "Choose a city first.");
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API}/blueprint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), birth_date: date, birth_time: time, city_id: city.id }),
      });
      if (!response.ok) throw new Error();
      setResult(await response.json());
    } catch {
      setError(lang === "id" ? "Data belum berhasil dihitung. Periksa format tanggal." : "Could not calculate. Check the date format.");
    } finally {
      setLoading(false);
    }
  };

  if (result) return (
    <SafeAreaView style={s.safe}>
      <ScrollView contentContainerStyle={s.content}>
        <Header lang={lang} toggle={toggle} />
        <Pressable testID="back-button" onPress={() => setResult(null)} style={s.back}>
          <Ionicons name="arrow-back" size={18} color={C.forest} />
          <Text style={s.backText}>{t.again}</Text>
        </Pressable>
        <Text style={s.eyebrow}>CETAK BIRU / BLUEPRINT</Text>
        <Text testID="result-heading" style={s.title}>{t.resultHeading}</Text>
        <Text testID="result-name" style={s.place}>
          {result.name} · {result.city.name}, {result.city.country} · {result.birth_date} · {result.birth_time}
        </Text>
        <View style={s.grid}>
          {([["TYPE", result.type, "result-type"], ["AUTHORITY", result.authority, "result-authority"], ["PROFILE", result.profile, "result-profile"], ["STRATEGY", result.strategy, "result-strategy"]] as string[][]).map(item => (
            <View key={item[0]} style={s.card}>
              <Text style={s.label}>{item[0]}</Text>
              <Text testID={item[2]} style={s.value}>{item[1]}</Text>
            </View>
          ))}
        </View>
        <View style={s.callout}>
          <Ionicons name="sparkles-outline" size={24} color={C.accent} />
          <Text style={s.calloutText}>
            {lang === "id"
              ? "Dihitung dari posisi 13 tubuh langit saat lahir dan 88° matahari sebelum lahir."
              : "Calculated from 13 celestial bodies at birth and 88° of solar arc before birth."}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={s.safe}>
      <ScrollView contentContainerStyle={s.content}>
        <Header lang={lang} toggle={toggle} />
        <View style={s.progress}>
          <Text style={s.active}>01 DATA</Text>
          <Text style={s.muted}>— 02 KOTA — 03 HASIL</Text>
        </View>
        <Text style={s.eyebrow}>CETAK BIRU / HUMAN DESIGN</Text>
        <Text style={s.title}>{t.title}</Text>
        <Text style={s.intro}>{t.intro}</Text>
        <View style={s.form}>
          <Field label={t.name} value={name} onChange={setName} testID="birth-name-input" placeholder={t.name} />
          <Field label={t.date} value={date} onChange={setDate} testID="birth-date-input" placeholder="DD-MM-YYYY" />
          <Field label={t.time} value={time} onChange={setTime} testID="birth-time-input" placeholder="HH:MM" />
          <Text style={s.label}>{t.city}</Text>
          <Pressable testID="city-picker-open-button" style={s.cityButton} onPress={() => setPicker(true)}>
            <Ionicons name="location-outline" size={20} color={C.accent} />
            <Text style={[s.cityText, !city && s.placeholder]}>{city ? `${city.name}, ${city.country}` : t.choose}</Text>
            <Ionicons name="chevron-down" size={18} color={C.muted} />
          </Pressable>
          <Text style={s.helper}>{t.helper}</Text>
        </View>
        {error ? <Text testID="blueprint-error" style={s.error}>{error}</Text> : null}
        <Pressable testID="birth-form-submit-button" style={[s.primary, loading && s.disabled]} onPress={submit} disabled={loading}>
          {loading ? <ActivityIndicator color={C.white} /> : (
            <>
              <Text style={s.primaryText}>{t.submit}</Text>
              <Ionicons name="arrow-forward" size={20} color={C.white} />
            </>
          )}
        </Pressable>
      </ScrollView>
      <Modal visible={picker} transparent animationType="slide">
        <View style={s.shade}>
          <View style={s.sheet}>
            <View style={s.handle} />
            <View style={s.sheetHeader}>
              <Text style={s.sheetTitle}>{t.choose}</Text>
              <Pressable testID="city-picker-close-button" onPress={() => { setPicker(false); setQuery(""); }}>
                <Ionicons name="close" size={24} color={C.ink} />
              </Pressable>
            </View>
            <TextInput
              testID="city-search-input"
              value={query}
              onChangeText={setQuery}
              placeholder={t.search}
              placeholderTextColor={C.muted}
              style={s.search}
              autoCorrect={false}
              autoCapitalize="none"
            />
            <ScrollView style={s.cityList} keyboardShouldPersistTaps="handled">
              {searching ? <ActivityIndicator color={C.forest} style={{ marginTop: 12 }} /> : null}
              {cities.map(item => (
                <Pressable testID={`city-option-${item.id}`} key={item.id} style={s.cityRow} onPress={() => { setCity(item); setPicker(false); setQuery(""); }}>
                  <View style={{ flex: 1 }}>
                    <Text style={s.cityName}>{item.name}</Text>
                    <Text style={s.cityCountry}>{item.country} · {item.timezone}</Text>
                  </View>
                  <Ionicons name="arrow-forward" size={18} color={C.accent} />
                </Pressable>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function Header({ lang, toggle }: { lang: Lang; toggle: () => void }) {
  return (
    <View style={s.header}>
      <View style={s.logo}>
        <View style={s.dot} />
        <Text testID="app-logo" style={s.logoText}>Cetak Biru</Text>
      </View>
      <Pressable testID="language-toggle" onPress={toggle} style={s.lang}>
        <Text style={s.langText}>{lang.toUpperCase()}</Text>
        <Ionicons name="swap-horizontal" size={16} color={C.forest} />
      </Pressable>
    </View>
  );
}

function Field({ label, value, onChange, testID, placeholder }: { label: string; value: string; onChange: (v: string) => void; testID: string; placeholder: string }) {
  return (
    <View>
      <Text style={s.label}>{label}</Text>
      <TextInput testID={testID} value={value} onChangeText={onChange} placeholder={placeholder} placeholderTextColor={C.muted} style={s.input} />
    </View>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.paper },
  content: { padding: 20, paddingBottom: 48 },
  header: { height: 56, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderBottomWidth: 1, borderBottomColor: C.deep, marginBottom: 28 },
  logo: { flexDirection: "row", alignItems: "center", gap: 8 },
  dot: { width: 14, height: 14, borderRadius: 7, backgroundColor: C.accent },
  logoText: { color: C.forest, fontSize: 20, fontWeight: "700" },
  lang: { minHeight: 44, paddingHorizontal: 12, flexDirection: "row", alignItems: "center", gap: 6, borderWidth: 1, borderColor: C.forest, borderRadius: 22 },
  langText: { color: C.forest, fontSize: 12, fontWeight: "700" },
  progress: { flexDirection: "row", gap: 8, marginBottom: 30 },
  active: { color: C.accent, fontSize: 11, fontWeight: "700", letterSpacing: 1 },
  muted: { color: C.muted, fontSize: 11, fontWeight: "600", letterSpacing: 1 },
  eyebrow: { color: C.accent, fontSize: 11, fontWeight: "700", letterSpacing: 2, marginBottom: 12 },
  title: { color: C.forest, fontSize: 36, lineHeight: 40, fontFamily: "Georgia", fontWeight: "600", marginBottom: 14 },
  intro: { color: C.muted, fontSize: 16, lineHeight: 25, marginBottom: 30 },
  form: { gap: 18 },
  label: { color: C.forest, fontSize: 12, fontWeight: "700", letterSpacing: 1, marginBottom: 8, textTransform: "uppercase" },
  input: { minHeight: 52, borderWidth: 1, borderColor: C.muted, backgroundColor: C.white, paddingHorizontal: 16, color: C.ink, fontSize: 16 },
  cityButton: { minHeight: 56, borderWidth: 1, borderColor: C.muted, backgroundColor: C.white, paddingHorizontal: 16, flexDirection: "row", alignItems: "center", gap: 12 },
  cityText: { flex: 1, color: C.ink, fontSize: 16 },
  placeholder: { color: C.muted },
  helper: { color: C.muted, fontSize: 13, lineHeight: 19 },
  error: { color: "#B14A3A", backgroundColor: "#F5E1DC", padding: 12, marginTop: 18 },
  primary: { minHeight: 56, backgroundColor: C.accent, marginTop: 28, flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 10 },
  disabled: { opacity: 0.7 },
  primaryText: { color: C.white, fontSize: 15, fontWeight: "800", letterSpacing: 1.5 },
  shade: { flex: 1, backgroundColor: "rgba(41,48,45,0.35)", justifyContent: "flex-end" },
  sheet: { backgroundColor: C.paper, padding: 20, paddingBottom: 30, height: "80%", borderTopLeftRadius: 24, borderTopRightRadius: 24 },
  handle: { width: 44, height: 4, backgroundColor: C.deep, alignSelf: "center", marginBottom: 20 },
  sheetHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  sheetTitle: { fontFamily: "Georgia", color: C.forest, fontSize: 26 },
  search: { minHeight: 48, backgroundColor: C.white, borderWidth: 1, borderColor: C.muted, paddingHorizontal: 14, fontSize: 16, marginBottom: 12 },
  cityList: { flex: 1 },
  cityRow: { minHeight: 60, borderBottomWidth: 1, borderBottomColor: C.deep, flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 8 },
  cityName: { color: C.ink, fontSize: 16, fontWeight: "600" },
  cityCountry: { color: C.muted, fontSize: 12, marginTop: 4 },
  back: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 44, marginBottom: 26 },
  backText: { color: C.forest, fontWeight: "600" },
  place: { color: C.muted, marginBottom: 24 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  card: { width: "48%", minHeight: 104, backgroundColor: C.white, borderWidth: 1, borderColor: C.deep, padding: 14, justifyContent: "space-between" },
  value: { color: C.forest, fontSize: 18, fontWeight: "700", lineHeight: 23 },
  callout: { flexDirection: "row", gap: 12, backgroundColor: C.accentSoft, padding: 18, marginTop: 18 },
  calloutText: { flex: 1, color: C.ink, fontSize: 15, lineHeight: 23 },
});
