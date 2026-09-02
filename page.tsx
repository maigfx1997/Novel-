"use client";

import { useState, useEffect, useCallback } from "react";

// ─── Types ─────────────────────────────────────────────────────────────────
type Lang = "ar" | "en" | "fr";
type Theme = "dark" | "light";
type SourceType = "wattpad" | "novlar" | "uranus";
type Format = "epub" | "txt";

interface Chapter {
  id: string;
  title: string;
  url: string;
  chapterNum: number;
  content?: string;
  images?: string[];
  included: boolean;
}

interface Novel {
  title: string;
  author: string;
  description: string;
  cover: string;
  sourceUrl: string;
  sourceType: SourceType;
  chapters: Chapter[];
}

interface SavedNovel {
  id: number;
  title: string;
  author: string;
  description: string;
  coverUrl: string;
  sourceUrl: string;
  sourceType: string;
  totalChapters: number;
  chapters: Chapter[];
  createdAt: string;
}

// ─── Translations ──────────────────────────────────────────────────────────
const t: Record<Lang, Record<string, string>> = {
  ar: {
    appTitle: "محوّل الروايات",
    appSubtitle: "حوّل روايتك إلى كتاب إلكتروني",
    enterUrl: "أدخل رابط الرواية",
    urlPlaceholder: "الصق رابط الرواية هنا...",
    fetchNovel: "جلب الرواية",
    fetching: "جارٍ الجلب...",
    supportedSites: "يدعم جميع المواقع",
    novelInfo: "معلومات الرواية",
    editTitle: "عنوان الرواية",
    editAuthor: "اسم الكاتب",
    editDesc: "الوصف / النبذة",
    changeCover: "تغيير الغلاف",
    coverUrl: "رابط الغلاف",
    chapters: "الفصول",
    chapter: "فصل",
    chapters_count: "فصول",
    loadContent: "تحميل المحتوى",
    loadAll: "تحميل جميع الفصول",
    loading: "جارٍ التحميل...",
    generate: "توليد الكتاب",
    generating: "جارٍ التوليد...",
    download: "تحميل",
    preview: "معاينة",
    previewBook: "معاينة الكتاب",
    close: "إغلاق",
    formats: "صيغة الملف",
    epub: "EPUB",
    txt: "نص",
    library: "المكتبة",
    libraryEmpty: "لا توجد روايات محفوظة",
    addToLibrary: "حفظ في المكتبة",
    delete: "حذف",
    deleteConfirm: "هل أنت متأكد من الحذف؟",
    selectAll: "تحديد الكل",
    deselectAll: "إلغاء التحديد",
    deleteChapter: "حذف الفصل",
    noContent: "لم يتم تحميل المحتوى",
    success: "تم بنجاح!",
    error: "حدث خطأ",
    saved: "تم الحفظ في المكتبة",
    deleted: "تم الحذف",
    theme: "الوضع",
    dark: "داكن",
    light: "فاتح",
    loadProgress: "جارٍ تحميل الفصول",
    included: "مضمّن",
    excluded: "محذوف",
    download_all: "تحميل الكل",
    download_selected: "تحميل المحدد",
    re_download: "إعادة التحميل",
    coverFromUrl: "أو أدخل رابط الغلاف:",
    uploadCover: "رفع صورة الغلاف",
    noChapters: "لم يتم العثور على فصول",
    addedDate: "تاريخ الإضافة",
    chaptersNum: "عدد الفصول",
    viewLibrary: "عرض المكتبة",
    backToFetch: "العودة",
    loadChapter: "تحميل",
    contentLoaded: "محمّل",
    contentNotLoaded: "لم يُحمّل",
    step1: "1. أدخل الرابط",
    step2: "2. عدّل وخصّص",
    step3: "3. حمّل الكتاب",
  },
  en: {
    appTitle: "Novel Converter",
    appSubtitle: "Convert your novel to an ebook",
    enterUrl: "Enter novel URL",
    urlPlaceholder: "Paste the novel URL here...",
    fetchNovel: "Fetch Novel",
    fetching: "Fetching...",
    supportedSites: "Supports all sites",
    novelInfo: "Novel Information",
    editTitle: "Novel Title",
    editAuthor: "Author Name",
    editDesc: "Description / Synopsis",
    changeCover: "Change Cover",
    coverUrl: "Cover URL",
    chapters: "Chapters",
    chapter: "Chapter",
    chapters_count: "chapters",
    loadContent: "Load Content",
    loadAll: "Load All Chapters",
    loading: "Loading...",
    generate: "Generate Book",
    generating: "Generating...",
    download: "Download",
    preview: "Preview",
    previewBook: "Book Preview",
    close: "Close",
    formats: "File Format",
    epub: "EPUB",
    txt: "Text",
    library: "Library",
    libraryEmpty: "No saved novels",
    addToLibrary: "Save to Library",
    delete: "Delete",
    deleteConfirm: "Are you sure you want to delete?",
    selectAll: "Select All",
    deselectAll: "Deselect All",
    deleteChapter: "Delete Chapter",
    noContent: "Content not loaded",
    success: "Success!",
    error: "An error occurred",
    saved: "Saved to library",
    deleted: "Deleted",
    theme: "Theme",
    dark: "Dark",
    light: "Light",
    loadProgress: "Loading chapters",
    included: "Included",
    excluded: "Excluded",
    download_all: "Download All",
    download_selected: "Download Selected",
    re_download: "Re-download",
    coverFromUrl: "Or enter cover URL:",
    uploadCover: "Upload Cover",
    noChapters: "No chapters found",
    addedDate: "Added Date",
    chaptersNum: "Chapters Count",
    viewLibrary: "View Library",
    backToFetch: "Back",
    loadChapter: "Load",
    contentLoaded: "Loaded",
    contentNotLoaded: "Not Loaded",
    step1: "1. Enter URL",
    step2: "2. Edit & Customize",
    step3: "3. Download Book",
  },
  fr: {
    appTitle: "Convertisseur de Romans",
    appSubtitle: "Convertissez votre roman en ebook",
    enterUrl: "Entrez l'URL du roman",
    urlPlaceholder: "Collez l'URL du roman ici...",
    fetchNovel: "Récupérer le Roman",
    fetching: "Récupération...",
    supportedSites: "Supporte tous les sites",
    novelInfo: "Informations sur le Roman",
    editTitle: "Titre du Roman",
    editAuthor: "Nom de l'Auteur",
    editDesc: "Description / Synopsis",
    changeCover: "Changer la Couverture",
    coverUrl: "URL de la Couverture",
    chapters: "Chapitres",
    chapter: "Chapitre",
    chapters_count: "chapitres",
    loadContent: "Charger le Contenu",
    loadAll: "Charger Tous les Chapitres",
    loading: "Chargement...",
    generate: "Générer le Livre",
    generating: "Génération...",
    download: "Télécharger",
    preview: "Aperçu",
    previewBook: "Aperçu du Livre",
    close: "Fermer",
    formats: "Format de Fichier",
    epub: "EPUB",
    txt: "Texte",
    library: "Bibliothèque",
    libraryEmpty: "Aucun roman sauvegardé",
    addToLibrary: "Sauvegarder dans la Bibliothèque",
    delete: "Supprimer",
    deleteConfirm: "Êtes-vous sûr de vouloir supprimer?",
    selectAll: "Tout Sélectionner",
    deselectAll: "Tout Désélectionner",
    deleteChapter: "Supprimer le Chapitre",
    noContent: "Contenu non chargé",
    success: "Succès!",
    error: "Une erreur s'est produite",
    saved: "Sauvegardé dans la bibliothèque",
    deleted: "Supprimé",
    theme: "Thème",
    dark: "Sombre",
    light: "Clair",
    loadProgress: "Chargement des chapitres",
    included: "Inclus",
    excluded: "Exclu",
    download_all: "Tout Télécharger",
    download_selected: "Télécharger la Sélection",
    re_download: "Re-télécharger",
    coverFromUrl: "Ou entrez l'URL de couverture:",
    uploadCover: "Téléverser la Couverture",
    noChapters: "Aucun chapitre trouvé",
    addedDate: "Date d'Ajout",
    chaptersNum: "Nombre de Chapitres",
    viewLibrary: "Voir la Bibliothèque",
    backToFetch: "Retour",
    loadChapter: "Charger",
    contentLoaded: "Chargé",
    contentNotLoaded: "Non Chargé",
    step1: "1. Entrer l'URL",
    step2: "2. Modifier & Personnaliser",
    step3: "3. Télécharger le Livre",
  },
};

// ─── Toast Component ────────────────────────────────────────────────────────
function Toast({
  msg,
  type,
  onClose,
}: {
  msg: string;
  type: "success" | "error" | "info";
  onClose: () => void;
}) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const colors = {
    success: "bg-emerald-500",
    error: "bg-red-500",
    info: "bg-blue-500",
  };
  return (
    <div
      className={`toast ${colors[type]} text-white fade-in`}
      style={{ cursor: "pointer" }}
      onClick={onClose}
    >
      <span>{icons[type]}</span>
      <span>{msg}</span>
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────────────
export default function Home() {
  const [lang, setLang] = useState<Lang>("ar");
  const [theme, setTheme] = useState<Theme>("dark");
  const [activeTab, setActiveTab] = useState<"fetch" | "library">("fetch");

  const [url, setUrl] = useState("");
  const [novel, setNovel] = useState<Novel | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [selectedFormat, setSelectedFormat] = useState<Format>("epub");

  const [savedNovels, setSavedNovels] = useState<SavedNovel[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const [previewChapterIdx, setPreviewChapterIdx] = useState(0);
  const [showCoverEdit, setShowCoverEdit] = useState(false);
  const [newCoverUrl, setNewCoverUrl] = useState("");

  const [toasts, setToasts] = useState<
    { id: number; msg: string; type: "success" | "error" | "info" }[]
  >([]);

  const dir = lang === "ar" ? "rtl" : "ltr";
  const tr = (key: string) => t[lang][key] || key;

  const addToast = useCallback(
    (msg: string, type: "success" | "error" | "info" = "info") => {
      const id = Date.now();
      setToasts((prev) => [...prev, { id, msg, type }]);
    },
    []
  );

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.dir = dir;
    document.documentElement.lang = lang;
  }, [theme, dir, lang]);

  // Load library
  useEffect(() => {
    fetchLibrary();
  }, []);

  async function fetchLibrary() {
    try {
      const res = await fetch("/api/novels");
      if (res.ok) {
        const data = await res.json();
        setSavedNovels(data);
      }
    } catch {
      /* ignore */
    }
  }

  // ── Fetch Novel ────────────────────────────────────────────────────────────
  async function handleFetch() {
    if (!url.trim()) return;
    setIsFetching(true);
    setNovel(null);
    try {
      const res = await fetch("/api/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setNovel({
        ...data,
        chapters: data.chapters.map((ch: Chapter) => ({
          ...ch,
          included: true,
        })),
      });
      addToast(tr("success"), "success");
    } catch (e) {
      addToast(
        `${tr("error")}: ${e instanceof Error ? e.message : "Unknown"}`,
        "error"
      );
    } finally {
      setIsFetching(false);
    }
  }

  // ── Load Chapter Content ──────────────────────────────────────────────────
  async function loadChapterContent(
    idx: number
  ): Promise<{ content: string; images: string[] }> {
    if (!novel) return { content: "", images: [] };
    const chapter = novel.chapters[idx];
    try {
      const res = await fetch("/api/chapter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chapter,
          sourceType: novel.sourceType,
          sourceUrl: novel.sourceUrl,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      return data;
    } catch {
      return { content: `<p>${tr("noContent")}</p>`, images: [] };
    }
  }

  async function handleLoadAllChapters() {
    if (!novel) return;
    setLoadingChapters(true);
    setLoadingProgress(0);
    const updated = [...novel.chapters];
    for (let i = 0; i < updated.length; i++) {
      if (updated[i].included && !updated[i].content) {
        const data = await loadChapterContent(i);
        updated[i] = { ...updated[i], ...data };
        setNovel((prev) =>
          prev ? { ...prev, chapters: [...updated] } : null
        );
        setLoadingProgress(Math.round(((i + 1) / updated.length) * 100));
        await new Promise((r) => setTimeout(r, 300));
      }
    }
    setLoadingChapters(false);
    addToast(tr("success"), "success");
  }

  async function handleLoadSingleChapter(idx: number) {
    if (!novel) return;
    const data = await loadChapterContent(idx);
    setNovel((prev) => {
      if (!prev) return null;
      const chapters = [...prev.chapters];
      chapters[idx] = { ...chapters[idx], ...data };
      return { ...prev, chapters };
    });
  }

  // ── Generate Book ─────────────────────────────────────────────────────────
  async function handleGenerate() {
    if (!novel) return;
    const includedChapters = novel.chapters.filter(
      (ch) => ch.included && ch.content
    );
    if (includedChapters.length === 0) {
      addToast(tr("noContent"), "error");
      return;
    }
    setIsGenerating(true);
    try {
      const endpoint =
        selectedFormat === "epub" ? "/api/generate-epub" : "/api/generate-txt";
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: novel.title,
          author: novel.author,
          description: novel.description,
          cover: novel.cover,
          chapters: includedChapters.map((ch) => ({
            title: ch.title,
            content: ch.content || "",
          })),
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error);
      }
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${novel.title}.${selectedFormat}`;
      link.click();
      addToast(tr("success"), "success");
    } catch (e) {
      addToast(
        `${tr("error")}: ${e instanceof Error ? e.message : "Unknown"}`,
        "error"
      );
    } finally {
      setIsGenerating(false);
    }
  }

  // ── Save to Library ───────────────────────────────────────────────────────
  async function handleSaveToLibrary() {
    if (!novel) return;
    try {
      const res = await fetch("/api/novels", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(novel),
      });
      if (!res.ok) throw new Error("Failed to save");
      addToast(tr("saved"), "success");
      fetchLibrary();
    } catch (e) {
      addToast(
        `${tr("error")}: ${e instanceof Error ? e.message : ""}`,
        "error"
      );
    }
  }

  // ── Delete from Library ───────────────────────────────────────────────────
  async function handleDeleteNovel(id: number) {
    if (!confirm(tr("deleteConfirm"))) return;
    try {
      const res = await fetch("/api/novels", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      if (!res.ok) throw new Error("Failed");
      addToast(tr("deleted"), "success");
      fetchLibrary();
    } catch {
      addToast(tr("error"), "error");
    }
  }

  // ── Load saved novel into editor ──────────────────────────────────────────
  function loadSavedNovel(saved: SavedNovel) {
    setNovel({
      title: saved.title,
      author: saved.author,
      description: saved.description,
      cover: saved.coverUrl,
      sourceUrl: saved.sourceUrl,
      sourceType: saved.sourceType as SourceType,
      chapters: (saved.chapters || []).map((ch) => ({
        ...ch,
        included: (ch as Chapter).included !== false,
      })),
    });
    setActiveTab("fetch");
  }

  // ── Toggle chapter inclusion ──────────────────────────────────────────────
  function toggleChapter(idx: number) {
    setNovel((prev) => {
      if (!prev) return null;
      const chapters = [...prev.chapters];
      chapters[idx] = { ...chapters[idx], included: !chapters[idx].included };
      return { ...prev, chapters };
    });
  }

  function toggleAllChapters(include: boolean) {
    setNovel((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        chapters: prev.chapters.map((ch) => ({ ...ch, included: include })),
      };
    });
  }

  function deleteChapter(idx: number) {
    setNovel((prev) => {
      if (!prev) return null;
      const chapters = prev.chapters.filter((_, i) => i !== idx);
      return { ...prev, chapters };
    });
  }

  // ── Apply cover URL ───────────────────────────────────────────────────────
  function applyCover() {
    if (newCoverUrl.trim()) {
      setNovel((prev) =>
        prev ? { ...prev, cover: newCoverUrl.trim() } : null
      );
    }
    setShowCoverEdit(false);
    setNewCoverUrl("");
  }

  const includedCount = novel?.chapters.filter((c) => c.included).length || 0;
  const loadedCount =
    novel?.chapters.filter((c) => c.included && c.content).length || 0;
  const previewChapters = novel?.chapters.filter(
    (c) => c.included && c.content
  ) || [];

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          theme === "dark"
            ? "linear-gradient(135deg, #0f0f1a 0%, #1a0a2e 50%, #0f1a2e 100%)"
            : "linear-gradient(135deg, #f0f0ff 0%, #e8e0ff 50%, #f0f8ff 100%)",
        fontFamily: "'Tajawal', 'Cairo', sans-serif",
        direction: dir as "rtl" | "ltr",
      }}
    >
      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <header
        className="glass"
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          padding: "12px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          borderBottom: "1px solid var(--border)",
        }}
      >
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              fontSize: "28px",
              background:
                "linear-gradient(135deg, #a78bfa, #f59e0b)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            📚
          </div>
          <div>
            <h1
              style={{
                fontSize: "20px",
                fontWeight: 800,
                background: "linear-gradient(135deg, #a78bfa, #f59e0b)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              {tr("appTitle")}
            </h1>
            <p style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              {tr("supportedSites")}
            </p>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {/* Language */}
          <div style={{ display: "flex", gap: "4px" }}>
            {(["ar", "en", "fr"] as Lang[]).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                style={{
                  padding: "6px 12px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background:
                    lang === l
                      ? "var(--primary)"
                      : "rgba(255,255,255,0.05)",
                  color: lang === l ? "white" : "var(--text-muted)",
                  cursor: "pointer",
                  fontWeight: 600,
                  fontSize: "13px",
                  fontFamily: "inherit",
                  transition: "all 0.2s",
                }}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Theme */}
          <button
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            style={{
              padding: "8px 14px",
              borderRadius: "10px",
              border: "1px solid var(--border)",
              background: "rgba(255,255,255,0.05)",
              color: "var(--text-primary)",
              cursor: "pointer",
              fontSize: "18px",
              fontFamily: "inherit",
            }}
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>

          {/* Tabs */}
          {(["fetch", "library"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: "8px 16px",
                borderRadius: "10px",
                border: "none",
                background:
                  activeTab === tab
                    ? "linear-gradient(135deg, var(--primary), var(--primary-light))"
                    : "rgba(255,255,255,0.05)",
                color: "white",
                cursor: "pointer",
                fontWeight: 700,
                fontSize: "13px",
                fontFamily: "inherit",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              {tab === "fetch" ? "🔍" : "📖"}
              {tab === "fetch" ? tr("fetchNovel") : `${tr("library")} (${savedNovels.length})`}
            </button>
          ))}
        </div>
      </header>

      <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "24px 16px" }}>
        {/* ══ FETCH TAB ══════════════════════════════════════════════════════ */}
        {activeTab === "fetch" && (
          <div className="fade-in">
            {/* URL Input Section */}
            {!novel && (
              <div
                style={{
                  maxWidth: "700px",
                  margin: "60px auto",
                  textAlign: "center",
                }}
              >
                <div style={{ marginBottom: "40px" }}>
                  <h2
                    style={{
                      fontSize: "40px",
                      fontWeight: 900,
                      background:
                        "linear-gradient(135deg, #a78bfa, #f59e0b)",
                      WebkitBackgroundClip: "text",
                      WebkitTextFillColor: "transparent",
                      marginBottom: "12px",
                    }}
                  >
                    📚 {tr("appTitle")}
                  </h2>
                  <p
                    style={{
                      color: "var(--text-muted)",
                      fontSize: "16px",
                    }}
                  >
                    {tr("appSubtitle")}
                  </p>
                </div>

                {/* Steps */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    gap: "20px",
                    marginBottom: "40px",
                    flexWrap: "wrap",
                  }}
                >
                  {[tr("step1"), tr("step2"), tr("step3")].map((step, i) => (
                    <div
                      key={i}
                      style={{
                        padding: "12px 20px",
                        borderRadius: "12px",
                        background: "rgba(109,40,217,0.2)",
                        border: "1px solid rgba(109,40,217,0.4)",
                        color: "#a78bfa",
                        fontSize: "13px",
                        fontWeight: 600,
                      }}
                    >
                      {step}
                    </div>
                  ))}
                </div>

                {/* URL Input */}
                <div className="glass" style={{ padding: "32px", borderRadius: "20px" }}>
                  <label
                    style={{
                      display: "block",
                      marginBottom: "12px",
                      color: "var(--text-muted)",
                      fontWeight: 600,
                      fontSize: "14px",
                      textAlign: dir === "rtl" ? "right" : "left",
                    }}
                  >
                    {tr("enterUrl")}
                  </label>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleFetch()}
                      placeholder={tr("urlPlaceholder")}
                      style={{
                        flex: 1,
                        padding: "14px 18px",
                        borderRadius: "12px",
                        border: "2px solid var(--border)",
                        background: "rgba(255,255,255,0.05)",
                        color: "var(--text-primary)",
                        fontSize: "14px",
                        fontFamily: "inherit",
                        direction: "ltr",
                        textAlign: "left",
                        outline: "none",
                      }}
                    />
                    <button
                      onClick={handleFetch}
                      disabled={isFetching || !url.trim()}
                      style={{
                        padding: "14px 24px",
                        borderRadius: "12px",
                        border: "none",
                        background:
                          "linear-gradient(135deg, var(--primary), var(--primary-light))",
                        color: "white",
                        fontWeight: 700,
                        fontSize: "14px",
                        cursor: isFetching ? "not-allowed" : "pointer",
                        opacity: isFetching || !url.trim() ? 0.7 : 1,
                        fontFamily: "inherit",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {isFetching ? (
                        <>
                          <span className="spinner" style={{ width: "18px", height: "18px" }} />
                          {tr("fetching")}
                        </>
                      ) : (
                        <>🔍 {tr("fetchNovel")}</>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Novel Editor */}
            {novel && (
              <div className="fade-in">
                {/* Back button + Save */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "20px",
                    flexWrap: "wrap",
                    gap: "10px",
                  }}
                >
                  <button
                    onClick={() => { setNovel(null); setUrl(""); }}
                    style={{
                      padding: "10px 20px",
                      borderRadius: "10px",
                      border: "1px solid var(--border)",
                      background: "rgba(255,255,255,0.05)",
                      color: "var(--text-muted)",
                      cursor: "pointer",
                      fontFamily: "inherit",
                      fontWeight: 600,
                      fontSize: "14px",
                    }}
                  >
                    ← {tr("backToFetch")}
                  </button>
                  <button
                    onClick={handleSaveToLibrary}
                    style={{
                      padding: "10px 20px",
                      borderRadius: "10px",
                      border: "none",
                      background: "linear-gradient(135deg, #10b981, #059669)",
                      color: "white",
                      cursor: "pointer",
                      fontFamily: "inherit",
                      fontWeight: 700,
                      fontSize: "14px",
                    }}
                  >
                    💾 {tr("addToLibrary")}
                  </button>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "minmax(280px, 380px) 1fr",
                    gap: "20px",
                    alignItems: "start",
                  }}
                >
                  {/* ── Left Panel: Novel Info ───────────────────────────── */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                    {/* Cover */}
                    <div
                      className="glass"
                      style={{
                        borderRadius: "16px",
                        padding: "20px",
                        textAlign: "center",
                      }}
                    >
                      <div style={{ position: "relative", display: "inline-block" }}>
                        {novel.cover ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={novel.cover}
                            alt={novel.title}
                            style={{
                              width: "160px",
                              height: "240px",
                              objectFit: "cover",
                              borderRadius: "12px",
                              boxShadow: "0 8px 30px rgba(0,0,0,0.4)",
                            }}
                            onError={(e) => {
                              (e.target as HTMLImageElement).src =
                                "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYwIiBoZWlnaHQ9IjI0MCIgdmlld0JveD0iMCAwIDE2MCAyNDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjE2MCIgaGVpZ2h0PSIyNDAiIGZpbGw9IiM2ZDI4ZDkiIHJ4PSIxMiIvPjx0ZXh0IHg9IjgwIiB5PSIxMjAiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjQwIj7wn5SYTm8gQ292ZXI8L3RleHQ+PC9zdmc+";
                            }}
                          />
                        ) : (
                          <div
                            style={{
                              width: "160px",
                              height: "240px",
                              borderRadius: "12px",
                              background:
                                "linear-gradient(135deg, var(--primary), var(--primary-light))",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: "50px",
                              margin: "0 auto",
                            }}
                          >
                            📚
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => setShowCoverEdit(true)}
                        style={{
                          marginTop: "12px",
                          padding: "8px 16px",
                          borderRadius: "8px",
                          border: "1px solid var(--border)",
                          background: "rgba(255,255,255,0.05)",
                          color: "var(--text-muted)",
                          cursor: "pointer",
                          fontSize: "13px",
                          fontFamily: "inherit",
                          width: "100%",
                        }}
                      >
                        🖼️ {tr("changeCover")}
                      </button>
                    </div>

                    {/* Edit Fields */}
                    <div
                      className="glass"
                      style={{ borderRadius: "16px", padding: "20px" }}
                    >
                      <h3
                        style={{
                          fontWeight: 700,
                          marginBottom: "16px",
                          color: "#a78bfa",
                          fontSize: "15px",
                        }}
                      >
                        ✏️ {tr("novelInfo")}
                      </h3>

                      {/* Title */}
                      <div style={{ marginBottom: "12px" }}>
                        <label
                          style={{
                            fontSize: "12px",
                            color: "var(--text-muted)",
                            marginBottom: "4px",
                            display: "block",
                          }}
                        >
                          {tr("editTitle")}
                        </label>
                        <input
                          value={novel.title}
                          onChange={(e) =>
                            setNovel((p) =>
                              p ? { ...p, title: e.target.value } : null
                            )
                          }
                          style={{
                            width: "100%",
                            padding: "10px 12px",
                            borderRadius: "8px",
                            border: "1px solid var(--border)",
                            background: "rgba(255,255,255,0.05)",
                            color: "var(--text-primary)",
                            fontSize: "14px",
                            fontFamily: "inherit",
                            outline: "none",
                          }}
                        />
                      </div>

                      {/* Author */}
                      <div style={{ marginBottom: "12px" }}>
                        <label
                          style={{
                            fontSize: "12px",
                            color: "var(--text-muted)",
                            marginBottom: "4px",
                            display: "block",
                          }}
                        >
                          {tr("editAuthor")}
                        </label>
                        <input
                          value={novel.author}
                          onChange={(e) =>
                            setNovel((p) =>
                              p ? { ...p, author: e.target.value } : null
                            )
                          }
                          style={{
                            width: "100%",
                            padding: "10px 12px",
                            borderRadius: "8px",
                            border: "1px solid var(--border)",
                            background: "rgba(255,255,255,0.05)",
                            color: "var(--text-primary)",
                            fontSize: "14px",
                            fontFamily: "inherit",
                            outline: "none",
                          }}
                        />
                      </div>

                      {/* Description */}
                      <div>
                        <label
                          style={{
                            fontSize: "12px",
                            color: "var(--text-muted)",
                            marginBottom: "4px",
                            display: "block",
                          }}
                        >
                          {tr("editDesc")}
                        </label>
                        <textarea
                          value={novel.description}
                          onChange={(e) =>
                            setNovel((p) =>
                              p ? { ...p, description: e.target.value } : null
                            )
                          }
                          rows={5}
                          style={{
                            width: "100%",
                            padding: "10px 12px",
                            borderRadius: "8px",
                            border: "1px solid var(--border)",
                            background: "rgba(255,255,255,0.05)",
                            color: "var(--text-primary)",
                            fontSize: "14px",
                            fontFamily: "inherit",
                            outline: "none",
                            resize: "vertical",
                          }}
                        />
                      </div>
                    </div>

                    {/* Download Panel */}
                    <div
                      className="glass"
                      style={{ borderRadius: "16px", padding: "20px" }}
                    >
                      <h3
                        style={{
                          fontWeight: 700,
                          marginBottom: "16px",
                          color: "#f59e0b",
                          fontSize: "15px",
                        }}
                      >
                        📥 {tr("formats")}
                      </h3>

                      <div
                        style={{ display: "flex", gap: "8px", marginBottom: "16px" }}
                      >
                        {(["epub", "txt"] as Format[]).map((fmt) => (
                          <button
                            key={fmt}
                            onClick={() => setSelectedFormat(fmt)}
                            style={{
                              flex: 1,
                              padding: "10px",
                              borderRadius: "10px",
                              border:
                                selectedFormat === fmt
                                  ? "2px solid var(--accent)"
                                  : "1px solid var(--border)",
                              background:
                                selectedFormat === fmt
                                  ? "rgba(245,158,11,0.15)"
                                  : "rgba(255,255,255,0.05)",
                              color:
                                selectedFormat === fmt
                                  ? "#f59e0b"
                                  : "var(--text-muted)",
                              cursor: "pointer",
                              fontWeight: 700,
                              fontSize: "13px",
                              fontFamily: "inherit",
                            }}
                          >
                            {fmt === "epub" ? "📕" : "📄"} {tr(fmt)}
                          </button>
                        ))}
                      </div>

                      {/* Progress info */}
                      <div
                        style={{
                          fontSize: "12px",
                          color: "var(--text-muted)",
                          marginBottom: "12px",
                        }}
                      >
                        {loadedCount}/{includedCount} {tr("chapters_count")} {tr("contentLoaded")}
                      </div>

                      {/* Load All Button */}
                      <button
                        onClick={handleLoadAllChapters}
                        disabled={loadingChapters}
                        style={{
                          width: "100%",
                          padding: "12px",
                          borderRadius: "10px",
                          border: "none",
                          background:
                            "linear-gradient(135deg, #3b82f6, #6366f1)",
                          color: "white",
                          fontWeight: 700,
                          fontSize: "13px",
                          cursor: loadingChapters ? "not-allowed" : "pointer",
                          opacity: loadingChapters ? 0.7 : 1,
                          marginBottom: "8px",
                          fontFamily: "inherit",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "8px",
                        }}
                      >
                        {loadingChapters ? (
                          <>
                            <span className="spinner" style={{ width: "16px", height: "16px" }} />
                            {tr("loadProgress")} {loadingProgress}%
                          </>
                        ) : (
                          <>📥 {tr("loadAll")}</>
                        )}
                      </button>

                      {loadingChapters && (
                        <div className="progress-bar" style={{ marginBottom: "8px" }}>
                          <div
                            className="progress-fill"
                            style={{ width: `${loadingProgress}%` }}
                          />
                        </div>
                      )}

                      {/* Preview Button */}
                      {loadedCount > 0 && (
                        <button
                          onClick={() => {
                            setPreviewChapterIdx(0);
                            setShowPreview(true);
                          }}
                          style={{
                            width: "100%",
                            padding: "12px",
                            borderRadius: "10px",
                            border: "1px solid var(--border)",
                            background: "rgba(255,255,255,0.05)",
                            color: "var(--text-muted)",
                            fontWeight: 600,
                            fontSize: "13px",
                            cursor: "pointer",
                            marginBottom: "8px",
                            fontFamily: "inherit",
                          }}
                        >
                          👁️ {tr("preview")}
                        </button>
                      )}

                      {/* Generate Button */}
                      <button
                        onClick={handleGenerate}
                        disabled={isGenerating || loadedCount === 0}
                        style={{
                          width: "100%",
                          padding: "14px",
                          borderRadius: "10px",
                          border: "none",
                          background:
                            loadedCount === 0
                              ? "rgba(255,255,255,0.1)"
                              : "linear-gradient(135deg, #f59e0b, #ef4444)",
                          color: "white",
                          fontWeight: 800,
                          fontSize: "15px",
                          cursor:
                            isGenerating || loadedCount === 0
                              ? "not-allowed"
                              : "pointer",
                          opacity: isGenerating || loadedCount === 0 ? 0.5 : 1,
                          fontFamily: "inherit",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "8px",
                        }}
                      >
                        {isGenerating ? (
                          <>
                            <span className="spinner" style={{ width: "18px", height: "18px" }} />
                            {tr("generating")}
                          </>
                        ) : (
                          <>🚀 {tr("generate")}</>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* ── Right Panel: Chapters ────────────────────────────── */}
                  <div>
                    <div
                      className="glass"
                      style={{ borderRadius: "16px", padding: "20px" }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "16px",
                          flexWrap: "wrap",
                          gap: "8px",
                        }}
                      >
                        <h3
                          style={{
                            fontWeight: 700,
                            color: "#a78bfa",
                            fontSize: "15px",
                          }}
                        >
                          📑 {tr("chapters")} ({novel.chapters.length})
                        </h3>
                        <div style={{ display: "flex", gap: "8px" }}>
                          <button
                            onClick={() => toggleAllChapters(true)}
                            style={{
                              padding: "6px 12px",
                              borderRadius: "8px",
                              border: "1px solid var(--border)",
                              background: "rgba(16,185,129,0.1)",
                              color: "#10b981",
                              cursor: "pointer",
                              fontSize: "12px",
                              fontFamily: "inherit",
                              fontWeight: 600,
                            }}
                          >
                            ✅ {tr("selectAll")}
                          </button>
                          <button
                            onClick={() => toggleAllChapters(false)}
                            style={{
                              padding: "6px 12px",
                              borderRadius: "8px",
                              border: "1px solid var(--border)",
                              background: "rgba(239,68,68,0.1)",
                              color: "#ef4444",
                              cursor: "pointer",
                              fontSize: "12px",
                              fontFamily: "inherit",
                              fontWeight: 600,
                            }}
                          >
                            ❌ {tr("deselectAll")}
                          </button>
                        </div>
                      </div>

                      {novel.chapters.length === 0 ? (
                        <div
                          style={{
                            textAlign: "center",
                            padding: "40px",
                            color: "var(--text-muted)",
                          }}
                        >
                          📭 {tr("noChapters")}
                        </div>
                      ) : (
                        <div
                          style={{
                            maxHeight: "600px",
                            overflowY: "auto",
                            paddingRight: "4px",
                          }}
                        >
                          {novel.chapters.map((ch, idx) => (
                            <div
                              key={ch.id}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "10px",
                                padding: "10px 12px",
                                borderRadius: "10px",
                                marginBottom: "6px",
                                background: ch.included
                                  ? "rgba(109,40,217,0.1)"
                                  : "rgba(255,255,255,0.02)",
                                border: `1px solid ${ch.included ? "rgba(109,40,217,0.3)" : "var(--border)"}`,
                                opacity: ch.included ? 1 : 0.5,
                                transition: "all 0.2s",
                              }}
                            >
                              {/* Checkbox */}
                              <input
                                type="checkbox"
                                checked={ch.included}
                                onChange={() => toggleChapter(idx)}
                                style={{ cursor: "pointer", accentColor: "var(--primary)" }}
                              />

                              {/* Chapter info */}
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div
                                  style={{
                                    fontSize: "13px",
                                    fontWeight: 700,
                                    color: "var(--text-primary)",
                                    whiteSpace: "nowrap",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                  }}
                                >
                                  {ch.title}
                                </div>
                                <div
                                  style={{
                                    fontSize: "11px",
                                    color: "var(--text-muted)",
                                    marginTop: "2px",
                                  }}
                                >
                                  {ch.content ? (
                                    <span style={{ color: "#10b981" }}>
                                      ✅ {tr("contentLoaded")}
                                    </span>
                                  ) : (
                                    <span style={{ color: "var(--text-muted)" }}>
                                      ⚪ {tr("contentNotLoaded")}
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Load button */}
                              {!ch.content && ch.included && (
                                <button
                                  onClick={() => handleLoadSingleChapter(idx)}
                                  style={{
                                    padding: "5px 10px",
                                    borderRadius: "6px",
                                    border: "none",
                                    background: "rgba(59,130,246,0.2)",
                                    color: "#60a5fa",
                                    cursor: "pointer",
                                    fontSize: "11px",
                                    fontFamily: "inherit",
                                    fontWeight: 600,
                                    whiteSpace: "nowrap",
                                  }}
                                >
                                  ⬇️ {tr("loadChapter")}
                                </button>
                              )}

                              {/* Delete button */}
                              <button
                                onClick={() => deleteChapter(idx)}
                                title={tr("deleteChapter")}
                                style={{
                                  padding: "5px 8px",
                                  borderRadius: "6px",
                                  border: "none",
                                  background: "rgba(239,68,68,0.1)",
                                  color: "#ef4444",
                                  cursor: "pointer",
                                  fontSize: "12px",
                                }}
                              >
                                🗑️
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══ LIBRARY TAB ════════════════════════════════════════════════════ */}
        {activeTab === "library" && (
          <div className="fade-in">
            <h2
              style={{
                fontSize: "24px",
                fontWeight: 800,
                marginBottom: "24px",
                background: "linear-gradient(135deg, #a78bfa, #f59e0b)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              📖 {tr("library")}
            </h2>

            {savedNovels.length === 0 ? (
              <div
                className="glass"
                style={{
                  padding: "80px 40px",
                  textAlign: "center",
                  borderRadius: "20px",
                }}
              >
                <div style={{ fontSize: "60px", marginBottom: "16px" }}>📭</div>
                <p style={{ color: "var(--text-muted)", fontSize: "16px" }}>
                  {tr("libraryEmpty")}
                </p>
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                  gap: "20px",
                }}
              >
                {savedNovels.map((saved) => (
                  <div
                    key={saved.id}
                    className="glass fade-in"
                    style={{
                      borderRadius: "16px",
                      overflow: "hidden",
                      transition: "transform 0.2s",
                    }}
                    onMouseEnter={(e) =>
                      ((e.currentTarget as HTMLDivElement).style.transform =
                        "translateY(-4px)")
                    }
                    onMouseLeave={(e) =>
                      ((e.currentTarget as HTMLDivElement).style.transform =
                        "translateY(0)")
                    }
                  >
                    {/* Cover */}
                    <div
                      style={{
                        height: "260px",
                        background:
                          "linear-gradient(135deg, var(--primary), var(--primary-light))",
                        position: "relative",
                        overflow: "hidden",
                      }}
                    >
                      {saved.coverUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={saved.coverUrl}
                          alt={saved.title}
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                          }}
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display =
                              "none";
                          }}
                        />
                      ) : (
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            height: "100%",
                            fontSize: "50px",
                          }}
                        >
                          📚
                        </div>
                      )}
                    </div>

                    {/* Info */}
                    <div style={{ padding: "14px" }}>
                      <div
                        style={{
                          fontWeight: 700,
                          fontSize: "13px",
                          marginBottom: "4px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          color: "var(--text-primary)",
                        }}
                      >
                        {saved.title}
                      </div>
                      <div
                        style={{
                          fontSize: "12px",
                          color: "var(--text-muted)",
                          marginBottom: "4px",
                        }}
                      >
                        {saved.author}
                      </div>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "#a78bfa",
                          marginBottom: "12px",
                        }}
                      >
                        {saved.totalChapters} {tr("chapters_count")}
                      </div>
                      <div style={{ display: "flex", gap: "6px" }}>
                        <button
                          onClick={() => loadSavedNovel(saved)}
                          style={{
                            flex: 1,
                            padding: "8px",
                            borderRadius: "8px",
                            border: "none",
                            background:
                              "linear-gradient(135deg, var(--primary), var(--primary-light))",
                            color: "white",
                            cursor: "pointer",
                            fontSize: "11px",
                            fontWeight: 700,
                            fontFamily: "inherit",
                          }}
                        >
                          ✏️ {tr("loadContent")}
                        </button>
                        <button
                          onClick={() => handleDeleteNovel(saved.id)}
                          style={{
                            padding: "8px 10px",
                            borderRadius: "8px",
                            border: "none",
                            background: "rgba(239,68,68,0.1)",
                            color: "#ef4444",
                            cursor: "pointer",
                            fontSize: "12px",
                          }}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* ── Cover Edit Modal ───────────────────────────────────────────────── */}
      {showCoverEdit && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.7)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => setShowCoverEdit(false)}
        >
          <div
            className="glass"
            style={{
              borderRadius: "20px",
              padding: "32px",
              maxWidth: "480px",
              width: "100%",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              style={{
                fontWeight: 700,
                marginBottom: "20px",
                fontSize: "18px",
                color: "#a78bfa",
              }}
            >
              🖼️ {tr("changeCover")}
            </h3>

            <label
              style={{
                fontSize: "13px",
                color: "var(--text-muted)",
                marginBottom: "8px",
                display: "block",
              }}
            >
              {tr("coverFromUrl")}
            </label>
            <input
              type="url"
              value={newCoverUrl}
              onChange={(e) => setNewCoverUrl(e.target.value)}
              placeholder="https://..."
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: "10px",
                border: "1px solid var(--border)",
                background: "rgba(255,255,255,0.05)",
                color: "var(--text-primary)",
                fontSize: "14px",
                fontFamily: "inherit",
                marginBottom: "16px",
                direction: "ltr",
                outline: "none",
              }}
            />

            <div style={{ display: "flex", gap: "10px" }}>
              <button
                onClick={applyCover}
                style={{
                  flex: 1,
                  padding: "12px",
                  borderRadius: "10px",
                  border: "none",
                  background:
                    "linear-gradient(135deg, var(--primary), var(--primary-light))",
                  color: "white",
                  fontWeight: 700,
                  cursor: "pointer",
                  fontFamily: "inherit",
                }}
              >
                ✅ {tr("success")}
              </button>
              <button
                onClick={() => setShowCoverEdit(false)}
                style={{
                  padding: "12px 20px",
                  borderRadius: "10px",
                  border: "1px solid var(--border)",
                  background: "rgba(255,255,255,0.05)",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  fontFamily: "inherit",
                }}
              >
                {tr("close")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Preview Modal ──────────────────────────────────────────────────── */}
      {showPreview && novel && previewChapters.length > 0 && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.85)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => setShowPreview(false)}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: "20px",
              maxWidth: "800px",
              width: "100%",
              maxHeight: "85vh",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              color: "#1a1a2e",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Preview Header */}
            <div
              style={{
                padding: "20px 24px",
                borderBottom: "1px solid #eee",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background:
                  "linear-gradient(135deg, var(--primary), var(--primary-light))",
                color: "white",
              }}
            >
              <div>
                <h3 style={{ fontWeight: 800, fontSize: "16px" }}>
                  {tr("previewBook")}: {novel.title}
                </h3>
                <p style={{ fontSize: "12px", opacity: 0.8 }}>
                  {previewChapters[previewChapterIdx]?.title}
                </p>
              </div>
              <button
                onClick={() => setShowPreview(false)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  border: "none",
                  background: "rgba(255,255,255,0.2)",
                  color: "white",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontWeight: 700,
                }}
              >
                ✕ {tr("close")}
              </button>
            </div>

            {/* Chapter Navigation */}
            <div
              style={{
                padding: "12px 24px",
                borderBottom: "1px solid #eee",
                display: "flex",
                gap: "8px",
                overflowX: "auto",
                background: "#f9f9f9",
              }}
            >
              {previewChapters.map((ch, i) => (
                <button
                  key={ch.id}
                  onClick={() => setPreviewChapterIdx(i)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "8px",
                    border: "none",
                    background:
                      i === previewChapterIdx
                        ? "var(--primary)"
                        : "rgba(0,0,0,0.05)",
                    color: i === previewChapterIdx ? "white" : "#666",
                    cursor: "pointer",
                    fontSize: "12px",
                    fontWeight: 600,
                    fontFamily: "inherit",
                    whiteSpace: "nowrap",
                    flexShrink: 0,
                  }}
                >
                  {i + 1}
                </button>
              ))}
            </div>

            {/* Content */}
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "32px",
                lineHeight: 1.9,
                fontSize: "16px",
                direction: "rtl",
                textAlign: "right",
              }}
              dangerouslySetInnerHTML={{
                __html:
                  previewChapters[previewChapterIdx]?.content || "",
              }}
            />
          </div>
        </div>
      )}

      {/* ── Toast Container ────────────────────────────────────────────────── */}
      <div className="toast-container">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            msg={toast.msg}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  );
}
