const DATA_ROOT = "./data";
const STORAGE_KEY = "mystyle_selected_styles";
const BOOKMARK_STORAGE_KEY = "mystyle_saved_detail_keys";
const RECENT_STORAGE_KEY = "mystyle_recent_detail_keys";
const RECENT_LIMIT = 12;
const FALLBACK_IMAGE = "https://placehold.co/600x800?text=MyStyle";
const VALID_TABS = ["home", "trend", "weather"];

const refs = {
    currentStyles: document.getElementById("currentStyles"),
    styleOptions: document.getElementById("styleOptions"),
    overlay: document.getElementById("styleOverlay"),
    cancelStyle: document.getElementById("cancel-style"),
    saveStyle: document.getElementById("save-style"),
    itemsContainer: document.getElementById("itemsContainer"),
    itemsEmpty: document.getElementById("itemsEmpty"),
    historyBlock: document.getElementById("historyBlock"),
    historyContainer: document.getElementById("historyContainer"),
    savedBlock: document.getElementById("savedBlock"),
    savedContainer: document.getElementById("savedContainer"),
    weatherSource: document.getElementById("weatherSource"),
    weatherUpdated: document.getElementById("weatherUpdated"),
    weatherStale: document.getElementById("weatherStale"),
    weatherStats: document.getElementById("weatherStats"),
    weatherRulesBlock: document.getElementById("weatherRulesBlock"),
    weatherRules: document.getElementById("weatherRules"),
    weatherRecommendBlock: document.getElementById("weatherRecommendBlock"),
    weatherItems: document.getElementById("weatherItems"),
    trendList: document.getElementById("trendList"),
    trendUpdated: document.getElementById("trendUpdated"),
    trendSource: document.getElementById("trendSource"),
    detailOverlay: document.getElementById("itemDetailOverlay"),
    detailClose: document.getElementById("itemDetailClose"),
    detailImage: document.getElementById("detailImage"),
    detailName: document.getElementById("detailName"),
    detailPrice: document.getElementById("detailPrice"),
    detailCategory: document.getElementById("detailCategory"),
    detailStyles: document.getElementById("detailStyles"),
    detailDescription: document.getElementById("detailDescription"),
    detailMeta: document.getElementById("detailMeta"),
    detailShopButton: document.getElementById("detailShopButton"),
    detailBookmarkButton: document.getElementById("detailBookmarkButton"),
    detailNameBottom: document.getElementById("detailNameBottom"),
    detailPriceBottom: document.getElementById("detailPriceBottom"),
    detailCategoryBottom: document.getElementById("detailCategoryBottom"),
    detailStylesBottom: document.getElementById("detailStylesBottom"),
    detailDescriptionBottom: document.getElementById("detailDescriptionBottom"),
    detailMetaBottom: document.getElementById("detailMetaBottom"),
    detailShopButtonBottom: document.getElementById("detailShopButtonBottom"),
    detailBookmarkButtonBottom: document.getElementById("detailBookmarkButtonBottom")
};

const defaultData = {
    styles: ["ストリート系", "モード系", "Y2K", "地雷系"],
    items: [],
    weather: null,
    wiki: null,
    history: [],
    saved: []
};

const state = {
    availableStyles: [],
    selectedStyles: [],
    items: [],
    history: [],
    saved: [],
    weather: null,
    weatherRecommended: [],
    weatherRules: [],
    wiki: null,
    itemLookup: new Map(),
    bookmarkSet: new Set(),
    bookmarkKeys: [],
    savedView: [],
    recentKeys: [],
    recentList: []
};

const tabState = {
    active: resolveInitialTab()
};

async function loadJSON(path) {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to load ${path}`);
    return res.json();
}

function restoreSelectedStyles(available) {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        return parsed.filter(style => available.includes(style));
    } catch (err) {
        console.warn("Failed to restore styles", err);
        return [];
    }
}

function persistSelectedStyles(styles) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(styles));
    } catch (err) {
        console.warn("Failed to persist styles", err);
    }
}

function resolveInitialTab() {
    if (typeof window === "undefined") return "home";
    const hash = window.location.hash?.replace("#", "");
    return isValidTab(hash) ? hash : "home";
}

function isValidTab(tab) {
    return VALID_TABS.includes(tab);
}

function updateTabHash(tab) {
    if (typeof window === "undefined" || !window.history?.replaceState) return;
    const base = window.location.pathname + window.location.search;
    const hash = tab === "home" ? "" : `#${tab}`;
    window.history.replaceState(null, "", `${base}${hash}`);
}

function restoreBookmarks() {
    try {
        const raw = localStorage.getItem(BOOKMARK_STORAGE_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
        console.warn("Failed to restore bookmarks", err);
        return [];
    }
}

function persistBookmarks() {
    try {
        localStorage.setItem(BOOKMARK_STORAGE_KEY, JSON.stringify(state.bookmarkKeys));
    } catch (err) {
        console.warn("Failed to persist bookmarks", err);
    }
}

function restoreRecents() {
    try {
        const raw = localStorage.getItem(RECENT_STORAGE_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
        console.warn("Failed to restore recents", err);
        return [];
    }
}

function persistRecents() {
    try {
        localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(state.recentKeys));
    } catch (err) {
        console.warn("Failed to persist recents", err);
    }
}

function randomKey(prefix = "item") {
    return `${prefix}-${Math.random().toString(36).slice(2, 9)}`;
}

function ensureDetailKey(item) {
    if (!item) return null;
    if (!item.__detailKey) {
        const base =
            item.id ??
            item.document_id ??
            item.item_id ??
            item.slug ??
            item.detail_url ??
            item.name;
        item.__detailKey = base ? String(base) : randomKey();
    }
    state.itemLookup.set(item.__detailKey, item);
    return item.__detailKey;
}

function rebuildItemLookup() {
    state.itemLookup.clear();
    [state.items, state.history, state.saved].forEach(list => {
        list?.forEach(item => ensureDetailKey(item));
    });
}

function initBookmarks() {
    state.bookmarkKeys = restoreBookmarks().filter(Boolean);
    state.bookmarkSet = new Set(state.bookmarkKeys);
    if (!state.bookmarkKeys.length && state.saved.length) {
        const fallback = [];
        state.saved.forEach(item => {
            const key = ensureDetailKey(item);
            if (key && !fallback.includes(key)) fallback.push(key);
        });
        state.bookmarkKeys = fallback;
        state.bookmarkSet = new Set(fallback);
        persistBookmarks();
    }
    updateSavedView();
}

function updateSavedView() {
    const seen = new Set();
    const merged = [];
    state.bookmarkKeys.forEach(key => {
        if (seen.has(key)) return;
        const item = state.itemLookup.get(key);
        if (item) {
            merged.push(item);
            seen.add(key);
        }
    });
    state.savedView = merged;
    renderHistoryStrip(state.savedView, refs.savedContainer, refs.savedBlock);
}

function isBookmarked(item) {
    const key = ensureDetailKey(item);
    return key ? state.bookmarkSet.has(key) : false;
}

function toggleBookmark(item) {
    const key = ensureDetailKey(item);
    if (!key) return;
    if (state.bookmarkSet.has(key)) {
        state.bookmarkSet.delete(key);
        state.bookmarkKeys = state.bookmarkKeys.filter(existing => existing !== key);
    } else {
        state.bookmarkSet.add(key);
        state.bookmarkKeys = [key, ...state.bookmarkKeys.filter(existing => existing !== key)];
    }
    persistBookmarks();
    updateSavedView();
    updateBookmarkButtonState(item);
}

function initRecents() {
    const storedKeys = restoreRecents();
    let keys = storedKeys;
    if (!keys.length && state.history.length) {
        keys = state.history
            .map(item => ensureDetailKey(item))
            .filter(Boolean);
    }
    state.recentKeys = keys.slice(0, RECENT_LIMIT);
    syncRecentsList();
}

function syncRecentsList() {
    const seen = new Set();
    const items = [];
    state.recentKeys.forEach(key => {
        if (seen.has(key)) return;
        const item = state.itemLookup.get(key);
        if (item) {
            items.push(item);
            seen.add(key);
        }
    });
    state.recentList = items;
    renderHistoryStrip(state.recentList, refs.historyContainer, refs.historyBlock);
}

function recordRecent(item) {
    const key = ensureDetailKey(item);
    if (!key) return;
    const filtered = state.recentKeys.filter(existing => existing !== key);
    state.recentKeys = [key, ...filtered].slice(0, RECENT_LIMIT);
    persistRecents();
    syncRecentsList();
}

function renderCurrentStyles() {
    if (!state.selectedStyles.length) {
        refs.currentStyles.innerHTML = '<p style="font-size:0.9em; color:#888;">未設定</p>';
        return;
    }
    refs.currentStyles.innerHTML = state.selectedStyles.map(style => `<span class="tag-sharp">${style}</span>`).join("");
}

function renderStyleOptions() {
    refs.styleOptions.innerHTML = state.availableStyles
        .map(style => {
            const active = state.selectedStyles.includes(style);
            return `<button class="tag-btn${active ? " active" : ""}" data-style="${style}">${style}</button>`;
        })
        .join("");
}

function openModal() {
    refs.overlay.classList.remove("hidden");
    refs.overlay.querySelector(".modal").setAttribute("aria-hidden", "false");
}

function closeModal() {
    refs.overlay.classList.add("hidden");
    refs.overlay.querySelector(".modal").setAttribute("aria-hidden", "true");
}

function initModalHandlers() {
    document.querySelectorAll(".open-style-modal").forEach(el => el.addEventListener("click", openModal));
    refs.cancelStyle.addEventListener("click", closeModal);
    refs.overlay.addEventListener("click", evt => {
        if (evt.target === refs.overlay) closeModal();
    });

    refs.saveStyle.addEventListener("click", () => {
        const active = Array.from(refs.styleOptions.querySelectorAll(".tag-btn.active"))
            .map(btn => btn.dataset.style);
        state.selectedStyles = active;
        persistSelectedStyles(active);
        renderCurrentStyles();
        renderItems();
        closeModal();
    });

    refs.styleOptions.addEventListener("click", evt => {
        const target = evt.target;
        if (!target.classList.contains("tag-btn")) return;
        target.classList.toggle("active");
    });
}

function renderItems() {
    if (!state.items.length) {
        refs.itemsContainer.innerHTML = "<p class=\"muted\">items.json を配置してください。</p>";
        refs.itemsEmpty.style.display = "block";
        return;
    }

    const filtered = state.selectedStyles.length
        ? state.items.filter(item => item.styles?.some(style => state.selectedStyles.includes(style)))
        : state.items;

    const sorted = [...filtered].sort((a, b) => (b.popularity || 0) - (a.popularity || 0));

    refs.itemsContainer.innerHTML = sorted
        .map(item => {
            const key = ensureDetailKey(item);
            const title = item.name || "アイテム";
            const badge = item.styles?.length ? `<span class="badge-style">${item.styles.join(', ')}</span>` : "";
            return `
            <article class="item-card" data-item-id="${key}" tabindex="0" role="button" aria-label="アイテム詳細を開く">
                <figure class="img-wrapper">
                    ${badge}
                    <img src="${item.image_url || FALLBACK_IMAGE}" alt="${title}" loading="lazy">
                </figure>
                <div class="info">
                    <h4 class="name">${title}</h4>
                    <div class="card-footer">
                        <p class="price">${renderPriceWithUnit(item.price)}</p>
                        <span class="view-details-btn">VIEW DETAILS</span>
                    </div>
                </div>
            </article>
        `;
        })
        .join("");

    refs.itemsEmpty.style.display = sorted.length ? "none" : "block";
}

function renderHistoryStrip(list = [], container, block) {
    if (!list.length) {
        block.style.display = "none";
        container.innerHTML = "";
        return;
    }
    block.style.display = "block";
    container.innerHTML = list.map(buildHistoryCard).join("");
}

function resolveShopUrl(item) {
    return item?.shop_url || item?.detail_url || item?.url || null;
}

function renderWeather() {
    if (!state.weather) {
        refs.weatherSource.textContent = "Data Source: -";
        refs.weatherStats.innerHTML = "<div class=\"mini-card\">weather.json を配置してください。</div>";
        return;
    }

    const w = state.weather;
    refs.weatherSource.textContent = `Data Source: ${w.source || '-'} / Location: ${w.location?.name || '-'}`;
    refs.weatherUpdated.textContent = `Updated: ${formatDate(w.updated_at)}`;
    refs.weatherStale.style.display = w.stale ? "block" : "none";

    const stats = [
        { label: "現在", value: `${fmtNum(w.current_temp)}℃` },
        { label: "最高/最低", value: `${fmtNum(w.today_max)}℃ / ${fmtNum(w.today_min)}℃` },
        { label: "降水確率", value: `${fmtNum(w.precip_prob_max)}%` },
        { label: "風速", value: `${fmtNum(w.wind_max)} m/s` }
    ];
    refs.weatherStats.innerHTML = stats
        .map(stat => `<div class="mini-card">${stat.label}: ${stat.value}</div>`)
        .join("");

    refs.weatherRulesBlock.hidden = !state.weatherRules.length;
    refs.weatherRules.innerHTML = state.weatherRules.map(rule => `<li>${rule}</li>`).join("");

    refs.weatherRecommendBlock.hidden = !state.weatherRecommended.length;
    refs.weatherItems.innerHTML = state.weatherRecommended.map(buildHistoryCard).join("");
}

function renderTrends() {
    if (!refs.trendList) return;
    if (!state.wiki?.trends?.length) {
        refs.trendList.innerHTML = "<p class=\"muted\">wiki_trends.json を配置してください。</p>";
        if (refs.trendUpdated) refs.trendUpdated.textContent = "--";
        if (refs.trendSource) refs.trendSource.textContent = "-";
        return;
    }

    const wiki = state.wiki;
    if (refs.trendUpdated) refs.trendUpdated.textContent = formatDate(wiki.updated_at);
    if (refs.trendSource) refs.trendSource.textContent = wiki.source || "Wikimedia Pageviews";

    refs.trendList.innerHTML = wiki.trends
        .map((trend, index) => renderTrendAccordion(trend, index))
        .join("");
}

function renderTrendAccordion(trend, index) {
    const dirClass = typeof trend.growth === "number" && trend.growth < 0 ? "is-down" : "is-up";
    const first = trend.series?.[0]?.views ?? "-";
    const last = trend.series?.[trend.series.length - 1]?.views ?? "-";
    const growthPct = typeof trend.growth === "number" ? (trend.growth * 100).toFixed(1) : "-";
    const scoreBase = typeof trend.growth === "number" ? 100 + trend.growth * 50 : 100;
    const score = Number.isFinite(scoreBase) ? Math.max(0, scoreBase) : null;
    const scoreText = score !== null ? score.toFixed(1) : "-";
    const badge = typeof trend.growth === "number" && trend.growth < 0 ? '<span class="trend-badge">キープ</span>' : "";
    const wikiLink = trend.article ? `https://ja.wikipedia.org/wiki/${trend.article}` : "#";
    const topClass = index === 0 ? " is-top" : "";
    const scoreClass = index < 3 ? " is-top-score" : "";
    const openAttr = index === 0 ? " open" : "";
    const articleLabel = trend.article ? `<div class="trend-article">(${trend.article})</div>` : "";
    const itemsMarkup = renderTrendItems(trend);

    return `
        <details class="trend-card${topClass} ${dirClass}"${openAttr}>
            <summary class="trend-summary">
                <div class="trend-card-head">
                    <div class="trend-rank">${index + 1}</div>
                    <div class="trend-main">
                        <div class="trend-name-row">
                            <div class="trend-name">${trend.label || "-"}</div>
                            ${articleLabel}
                        </div>
                        <div class="trend-sub">7日推移: <span class="trend-pv">${first}</span> → <span class="trend-pv">${last}</span></div>
                    </div>
                    <div class="trend-metric">
                        <div class="trend-score${scoreClass}">${scoreText}</div>
                        <div class="trend-growth-small">前週比 ${growthPct}%</div>
                        ${badge}
                    </div>
                </div>
                <div class="trend-chevron">
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                </div>
            </summary>
            <div class="trend-card-foot">
                <a class="btn-trend" href="${wikiLink}" target="_blank" rel="noopener noreferrer">Wikipediaで詳しく</a>
            </div>
            <div class="trend-items-expander">
                ${itemsMarkup}
            </div>
        </details>
    `;
}

function renderTrendItems(trend) {
    const explicitItems = Array.isArray(trend.trend_items) ? trend.trend_items : [];
    const derived = explicitItems.length ? explicitItems : deriveTrendItems(trend.label);

    if (!derived.length) {
        const searchQuery = trend.label ? encodeURIComponent(`${trend.label} ファッション`) : "ファッション";
        return `
            <div class="trend-no-items">
                <p>関連アイテムが見つかりませんでした。</p>
                <a class="btn-trend-sm" href="https://www.google.com/search?q=${searchQuery}" target="_blank" rel="noopener noreferrer">検索してみる</a>
            </div>
        `;
    }

    return `
        <div class="trend-item-grid">
            ${derived.slice(0, 8).map(renderTrendItemThumb).join("")}
        </div>
    `;
}

function renderTrendItemThumb(item) {
    const key = ensureDetailKey(item);
    const brand = item.brand || item.store || "BRAND";
    const priceText = typeof item.price === "number" ? `¥${formatPrice(item.price)}` : "-";
    const hasImage = Boolean(item.image_url);
    const media = hasImage
        ? `<img src="${item.image_url}" alt="${item.name || brand}" loading="lazy">`
        : '<div class="no-img">No Img</div>';
    const href = resolveShopUrl(item) || item.detail_url || "#";

    return `
        <a class="trend-item-thumb" data-item-id="${key}" href="${href}" tabindex="0" role="button" aria-label="${item.name || brand} の詳細を開く">
            <div class="ti-img-box">${media}</div>
            <div class="ti-info">
                <div class="ti-brand">${brand}</div>
                <div class="ti-price">${priceText}</div>
            </div>
        </a>
    `;
}

function deriveTrendItems(label) {
    if (!state.items?.length || !label) return [];
    const tokens = buildTrendTokens(label);
    if (!tokens.length) return [];
    const matches = state.items.filter(item => matchesTrendTokens(item, tokens));
    return matches.slice(0, 8);
}

function buildTrendTokens(label) {
    const raw = normalizeTrendValue(label);
    if (!raw) return [];
    const withoutSuffix = raw.replace(/系$/u, "");
    const set = new Set([raw, withoutSuffix]);
    return [...set].filter(Boolean);
}

function normalizeTrendValue(value) {
    if (!value) return "";
    return String(value).toLowerCase().replace(/\s+/g, "");
}

function matchesTrendTokens(item, tokens) {
    const candidates = [];
    if (Array.isArray(item.styles)) {
        candidates.push(...item.styles);
    } else if (typeof item.styles === "string") {
        candidates.push(item.styles);
    }
    if (Array.isArray(item.tags)) {
        candidates.push(...item.tags);
    }
    if (item.category) candidates.push(item.category);
    if (Array.isArray(item.categories)) candidates.push(...item.categories);
    if (item.name) candidates.push(item.name);
    if (item.brand) candidates.push(item.brand);

    return candidates.some(candidate => {
        const normalized = normalizeTrendValue(candidate).replace(/系$/u, "");
        if (!normalized) return false;
        return tokens.some(token => normalized.includes(token) || token.includes(normalized));
    });
}

function fmtNum(value) {
    return typeof value === "number" && Number.isFinite(value) ? Math.round(value) : "-";
}

function formatPrice(value) {
    if (typeof value !== "number") return "-";
    return value.toLocaleString("ja-JP");
}

function renderPriceWithUnit(value) {
    return typeof value === "number" ? `${formatPrice(value)}<span class="currency">円</span>` : "-";
}

function formatDate(value) {
    if (!value) return "--";
    const date = typeof value === "string" ? new Date(value) : value;
    if (Number.isNaN(date.getTime())) return value;
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function deriveWeatherContext() {
    if (!state.weather || !state.items.length) {
        state.weatherRules = [];
        state.weatherRecommended = [];
        return;
    }

    const w = state.weather;
    const tagsFired = new Set();
    const rules = [];

    if (typeof w.precip_prob_max === "number" && w.precip_prob_max >= 40) {
        rules.push("降水確率40%以上なので撥水・防水アイテムを優先しています。");
        tagsFired.add("waterproof");
    }
    if (typeof w.today_max === "number" && w.today_max <= 12) {
        rules.push("最高気温12℃以下のため、防寒性の高いアウターをピックアップ。");
        tagsFired.add("outer");
    }
    if (typeof w.wind_max === "number" && w.wind_max >= 8) {
        rules.push("風速8m/s以上なので、防風仕様のアイテムを含めています。");
        tagsFired.add("windproof");
    }
    if (typeof w.today_max === "number" && typeof w.today_min === "number" && w.today_max - w.today_min >= 8) {
        rules.push("寒暖差が大きいため、レイヤリングしやすい構成を推奨します。");
        tagsFired.add("layering");
    }
    if (typeof w.today_max === "number" && w.today_max >= 25) {
        rules.push("25℃以上の見込みなので、通気性と速乾性を持つアイテムを表示します。");
        tagsFired.add("breathable");
    }

    state.weatherRules = rules;

    const scored = state.items
        .map(item => {
            const itemTags = item.weather_tags || [];
            const score = itemTags.reduce((acc, tag) => acc + (tagsFired.has(tag) ? 1 : 0), 0);
            return { item, score };
        })
        .filter(entry => entry.score > 0)
        .sort((a, b) => {
            if (b.score !== a.score) return b.score - a.score;
            return (b.item.popularity || 0) - (a.item.popularity || 0);
        })
        .slice(0, 10)
        .map(entry => entry.item);

    state.weatherRecommended = scored;
}

function buildHistoryCard(item) {
    const key = ensureDetailKey(item);
    const title = item.name || "アイテム";
    const media = item.image_url
        ? `<img src="${item.image_url}" loading="lazy" alt="${title}">`
        : '<div class="placeholder"></div>';
    const price = typeof item.price === "number"
        ? `${formatPrice(item.price)}<span style="font-size:0.75em; margin-left:2px;">円</span>`
        : "-";
    return `
        <div class="history-card" data-item-id="${key}" tabindex="0" role="button" aria-label="アイテム詳細を開く">
            ${media}
            <div class="history-meta">
                <div class="name">${title}</div>
                <div class="price">${price}</div>
            </div>
        </div>
    `;
}

function getActiveDetailItem() {
    const id = refs.detailOverlay?.dataset.activeItemId;
    return id ? state.itemLookup.get(id) : null;
}

function updateBookmarkButtonState(item) {
    if (!item) return;
    const buttons = [refs.detailBookmarkButton, refs.detailBookmarkButtonBottom].filter(Boolean);
    if (!buttons.length) return;
    const active = isBookmarked(item);
    buttons.forEach(button => {
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", String(active));
    });
}

function syncShopButton(item) {
    const buttons = [refs.detailShopButton, refs.detailShopButtonBottom].filter(Boolean);
    if (!buttons.length) return;
    const shopUrl = resolveShopUrl(item);
    buttons.forEach(button => {
        if (shopUrl) {
            button.href = shopUrl;
            button.classList.remove("is-disabled");
            button.setAttribute("aria-disabled", "false");
            button.textContent = "販売ページへ";
            button.target = "_blank";
            button.tabIndex = 0;
        } else {
            button.href = "#";
            button.classList.add("is-disabled");
            button.setAttribute("aria-disabled", "true");
            button.textContent = "SOLD OUT";
            button.target = "_self";
            button.tabIndex = -1;
        }
    });
}

function initTabs() {
    const tabButtons = document.querySelectorAll(".page-tabs .tab");
    const tabPanels = document.querySelectorAll(".tab-panel");
    const tabTargets = document.querySelectorAll("[data-tab-target]");

    const activate = (tab, options = {}) => {
        if (!isValidTab(tab)) tab = "home";
        tabState.active = tab;
        document.documentElement.dataset.activeTab = tab;
        document.body.dataset.activeTab = tab;
        tabButtons.forEach(btn => btn.classList.toggle("active", btn.dataset.tab === tab));
        tabPanels.forEach(panel => panel.classList.toggle("active", panel.dataset.panel === tab));
        if (!options.skipHash) updateTabHash(tab);
    };

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => activate(btn.dataset.tab));
    });

    tabTargets.forEach(el => {
        el.addEventListener("click", evt => {
            evt.preventDefault();
            activate(el.dataset.tabTarget);
        });
    });

    activate(tabState.active, { skipHash: true, force: true });

    window.addEventListener("hashchange", () => {
        const next = resolveInitialTab();
        activate(next, { skipHash: true, force: true });
    });
}

function handleItemActivation(evt) {
    const trigger = evt.target.closest("[data-item-id]");
    if (!trigger) return;
    evt.preventDefault();
    openDetailById(trigger.dataset.itemId);
}

function handleItemKeydown(evt) {
    if (evt.key !== "Enter" && evt.key !== " " && evt.key !== "Spacebar") return;
    const trigger = evt.target.closest("[data-item-id]");
    if (!trigger) return;
    evt.preventDefault();
    openDetailById(trigger.dataset.itemId);
}

function openDetailById(id) {
    if (!id) return;
    const item = state.itemLookup.get(id);
    if (!item) return;
    showDetailOverlay(item);
}

function showDetailOverlay(item) {
    if (!refs.detailOverlay) return;
    recordRecent(item);
    populateDetailOverlay(item);
    refs.detailOverlay.dataset.activeItemId = item.__detailKey;
    refs.detailOverlay.classList.remove("hidden");
    refs.detailOverlay.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    requestAnimationFrame(() => refs.detailClose?.focus());
}

function hideDetailOverlay() {
    if (!refs.detailOverlay) return;
    refs.detailOverlay.classList.add("hidden");
    refs.detailOverlay.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
    delete refs.detailOverlay.dataset.activeItemId;
}

function populateDetailOverlay(item) {
    if (!refs.detailImage) return;
    refs.detailImage.src = item.image_url || FALLBACK_IMAGE;
    refs.detailImage.alt = item.name || "";

    const title = item.name || "アイテム";
    refs.detailName.textContent = title;
    if (refs.detailNameBottom) refs.detailNameBottom.textContent = title;

    const priceText = typeof item.price === "number" ? `¥${formatPrice(item.price)}` : "-";
    refs.detailPrice.textContent = priceText;
    if (refs.detailPriceBottom) refs.detailPriceBottom.textContent = priceText;

    const category = item.category || item.categories?.join(", ") || "-";
    refs.detailCategory.textContent = category;
    if (refs.detailCategoryBottom) refs.detailCategoryBottom.textContent = category;

    const stylesHTML = item.styles?.length
        ? item.styles.map(style => `<span class="tag-sharp">${style}</span>`).join("")
        : '<span class="muted">スタイル情報なし</span>';
    refs.detailStyles.innerHTML = stylesHTML;
    if (refs.detailStylesBottom) refs.detailStylesBottom.innerHTML = stylesHTML;

    const description = item.description || item.caption || item.summary || "詳細情報はまだ登録されていません。";
    refs.detailDescription.textContent = description;
    if (refs.detailDescriptionBottom) refs.detailDescriptionBottom.textContent = description;

    const metaParts = [];
    if (item.brand) metaParts.push(`ブランド: ${item.brand}`);
    if (item.store) metaParts.push(`ショップ: ${item.store}`);
    if (item.gender) metaParts.push(`対象: ${item.gender}`);
    if (item.updated_at) metaParts.push(`更新: ${formatDate(item.updated_at)}`);
    const metaText = metaParts.join(" / ");
    refs.detailMeta.textContent = metaText;
    if (refs.detailMetaBottom) refs.detailMetaBottom.textContent = metaText;
    syncShopButton(item);
    updateBookmarkButtonState(item);
}

function initDetailOverlay() {
    if (!refs.detailOverlay) return;
    const containers = [
        refs.itemsContainer,
        refs.historyContainer,
        refs.savedContainer,
        refs.weatherItems,
        refs.trendList
    ];
    containers.forEach(container => {
        if (!container) return;
        container.addEventListener("click", handleItemActivation);
        container.addEventListener("keydown", handleItemKeydown);
    });

    refs.detailClose?.addEventListener("click", hideDetailOverlay);
    refs.detailOverlay.addEventListener("click", evt => {
        if (evt.target === refs.detailOverlay) hideDetailOverlay();
    });
    document.addEventListener("keydown", evt => {
        if (evt.key === "Escape" && !refs.detailOverlay.classList.contains("hidden")) {
            hideDetailOverlay();
        }
    });
    [refs.detailBookmarkButton, refs.detailBookmarkButtonBottom].forEach(button => {
        button?.addEventListener("click", () => {
            const current = getActiveDetailItem();
            if (current) toggleBookmark(current);
        });
    });
}

async function bootstrap() {
    try {
        const [styles, items, history, saved, weather, wiki] = await Promise.all([
            loadJSON(`${DATA_ROOT}/styles.json`).catch(() => ({ available_styles: defaultData.styles })),
            loadJSON(`${DATA_ROOT}/items.json`).catch(() => defaultData.items),
            loadJSON(`${DATA_ROOT}/history.json`).catch(() => defaultData.history),
            loadJSON(`${DATA_ROOT}/saved_items.json`).catch(() => defaultData.saved),
            loadJSON(`${DATA_ROOT}/weather.json`).catch(() => defaultData.weather),
            loadJSON(`${DATA_ROOT}/wiki_trends.json`).catch(() => defaultData.wiki)
        ]);

        state.availableStyles = styles.available_styles || defaultData.styles;
        state.items = Array.isArray(items) ? items : [];
        state.history = Array.isArray(history) ? history : [];
        state.saved = Array.isArray(saved) ? saved : [];
        state.weather = weather;
        state.wiki = wiki;

        state.selectedStyles = restoreSelectedStyles(state.availableStyles);
        if (!state.selectedStyles.length) {
            state.selectedStyles = state.availableStyles.slice(0, 3);
            persistSelectedStyles(state.selectedStyles);
        }

        rebuildItemLookup();
        initBookmarks();
        initRecents();
        renderCurrentStyles();
        renderStyleOptions();
        renderItems();
        deriveWeatherContext();
        renderWeather();
        renderTrends();
        initModalHandlers();
        initTabs();
        initDetailOverlay();
    } catch (err) {
        console.error("Failed to bootstrap static UI", err);
        refs.itemsContainer.innerHTML = `<p class="muted">初期化に失敗しました: ${err.message}</p>`;
    }
}

document.addEventListener("DOMContentLoaded", bootstrap);
