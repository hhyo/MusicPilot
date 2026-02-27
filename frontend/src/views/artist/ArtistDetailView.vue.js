"use strict";
/// <reference types="../../../../../../.npm/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="../../../../../../.npm/_npx/2db181330ea4b15b/node_modules/@vue/language-core/types/props-fallback.d.ts" />
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
var _a;
Object.defineProperty(exports, "__esModule", { value: true });
var vue_1 = require("vue");
var vue_router_1 = require("vue-router");
var ArtistAvatar_vue_1 = require("@/components/audio/ArtistAvatar.vue");
var AlbumCover_vue_1 = require("@/components/audio/AlbumCover.vue");
var TrackList_vue_1 = require("@/components/audio/TrackList.vue");
var Loading_vue_1 = require("@/components/common/Loading.vue");
var router = (0, vue_router_1.useRouter)();
var route = (0, vue_router_1.useRoute)();
var loading = (0, vue_1.ref)(false);
var albumsLoading = (0, vue_1.ref)(false);
var tracksLoading = (0, vue_1.ref)(false);
var artist = (0, vue_1.ref)(null);
var albums = (0, vue_1.ref)([]);
var tracks = (0, vue_1.ref)([]);
var responsiveCols = (0, vue_1.computed)(function () { return ({
    xs: 2,
    sm: 3,
    md: 4,
    lg: 5,
    xl: 6,
}); });
var artistId = (0, vue_1.computed)(function () { return Number(route.params.id); });
(0, vue_1.onMounted)(function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, loadArtist()];
            case 1:
                _a.sent();
                return [4 /*yield*/, loadAlbums()];
            case 2:
                _a.sent();
                return [4 /*yield*/, loadTracks()];
            case 3:
                _a.sent();
                return [2 /*return*/];
        }
    });
}); });
function loadArtist() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            loading.value = true;
            try {
                // TODO: 调用 artistApi.getById(artistId.value)
            }
            finally {
                loading.value = false;
            }
            return [2 /*return*/];
        });
    });
}
function loadAlbums() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            albumsLoading.value = true;
            try {
                // TODO: 调用 artist 的专辑 API
            }
            finally {
                albumsLoading.value = false;
            }
            return [2 /*return*/];
        });
    });
}
function loadTracks() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            tracksLoading.value = true;
            try {
                // TODO: 调用 trackApi.getByArtistId()
            }
            finally {
                tracksLoading.value = false;
            }
            return [2 /*return*/];
        });
    });
}
function goToAlbum(id) {
    router.push({ name: 'AlbumDetail', params: { id: id } });
}
function goBack() {
    router.back();
}
var __VLS_ctx = __assign(__assign({}, {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "artist-detail-view" }));
/** @type {__VLS_StyleScopedClasses['artist-detail-view']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader} */
nPageHeader;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0(__assign({ 'onBack': {} }, { title: "艺术家详情" })));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([__assign({ 'onBack': {} }, { title: "艺术家详情" })], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5;
var __VLS_6 = ({ back: {} },
    { onBack: (__VLS_ctx.goBack) });
var __VLS_3;
var __VLS_4;
var __VLS_7 = Loading_vue_1.default || Loading_vue_1.default;
// @ts-ignore
var __VLS_8 = __VLS_asFunctionalComponent1(__VLS_7, new __VLS_7({
    loading: (__VLS_ctx.loading),
    description: "加载中...",
}));
var __VLS_9 = __VLS_8.apply(void 0, __spreadArray([{
        loading: (__VLS_ctx.loading),
        description: "加载中...",
    }], __VLS_functionalComponentArgsRest(__VLS_8), false));
var __VLS_12 = __VLS_10.slots.default;
if (!__VLS_ctx.loading && !__VLS_ctx.artist) {
    var __VLS_13 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
    nEmpty;
    // @ts-ignore
    var __VLS_14 = __VLS_asFunctionalComponent1(__VLS_13, new __VLS_13({
        description: "艺术家不存在",
    }));
    var __VLS_15 = __VLS_14.apply(void 0, __spreadArray([{
            description: "艺术家不存在",
        }], __VLS_functionalComponentArgsRest(__VLS_14), false));
}
else if (__VLS_ctx.artist) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "artist-header" }));
    /** @type {__VLS_StyleScopedClasses['artist-header']} */ ;
    var __VLS_18 = ArtistAvatar_vue_1.default;
    // @ts-ignore
    var __VLS_19 = __VLS_asFunctionalComponent1(__VLS_18, new __VLS_18({
        avatarUrl: (__VLS_ctx.artist.image_url),
        name: (__VLS_ctx.artist.name),
        size: "large",
    }));
    var __VLS_20 = __VLS_19.apply(void 0, __spreadArray([{
            avatarUrl: (__VLS_ctx.artist.image_url),
            name: (__VLS_ctx.artist.name),
            size: "large",
        }], __VLS_functionalComponentArgsRest(__VLS_19), false));
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "artist-info" }));
    /** @type {__VLS_StyleScopedClasses['artist-info']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.h1, __VLS_intrinsics.h1)(__assign({ class: "artist-name" }));
    /** @type {__VLS_StyleScopedClasses['artist-name']} */ ;
    (__VLS_ctx.artist.name);
    if (__VLS_ctx.artist.biography) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)(__assign({ class: "artist-bio" }));
        /** @type {__VLS_StyleScopedClasses['artist-bio']} */ ;
        (__VLS_ctx.artist.biography);
    }
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "artist-tags" }));
    /** @type {__VLS_StyleScopedClasses['artist-tags']} */ ;
    for (var _i = 0, _b = __VLS_vFor(((__VLS_ctx.artist.genres || []))); _i < _b.length; _i++) {
        var genre = _b[_i][0];
        var __VLS_23 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
        nTag;
        // @ts-ignore
        var __VLS_24 = __VLS_asFunctionalComponent1(__VLS_23, new __VLS_23({
            key: (genre),
        }));
        var __VLS_25 = __VLS_24.apply(void 0, __spreadArray([{
                key: (genre),
            }], __VLS_functionalComponentArgsRest(__VLS_24), false));
        var __VLS_28 = __VLS_26.slots.default;
        (genre);
        // @ts-ignore
        [goBack, loading, loading, artist, artist, artist, artist, artist, artist, artist, artist,];
        var __VLS_26;
        // @ts-ignore
        [];
    }
    var __VLS_29 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
    nCard;
    // @ts-ignore
    var __VLS_30 = __VLS_asFunctionalComponent1(__VLS_29, new __VLS_29(__assign({ title: "专辑" }, { style: {} })));
    var __VLS_31 = __VLS_30.apply(void 0, __spreadArray([__assign({ title: "专辑" }, { style: {} })], __VLS_functionalComponentArgsRest(__VLS_30), false));
    var __VLS_34 = __VLS_32.slots.default;
    var __VLS_35 = Loading_vue_1.default || Loading_vue_1.default;
    // @ts-ignore
    var __VLS_36 = __VLS_asFunctionalComponent1(__VLS_35, new __VLS_35({
        loading: (__VLS_ctx.albumsLoading),
        description: "加载专辑中...",
    }));
    var __VLS_37 = __VLS_36.apply(void 0, __spreadArray([{
            loading: (__VLS_ctx.albumsLoading),
            description: "加载专辑中...",
        }], __VLS_functionalComponentArgsRest(__VLS_36), false));
    var __VLS_40 = __VLS_38.slots.default;
    if (!__VLS_ctx.albumsLoading && !__VLS_ctx.albums.length) {
        var __VLS_41 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
        nEmpty;
        // @ts-ignore
        var __VLS_42 = __VLS_asFunctionalComponent1(__VLS_41, new __VLS_41({
            description: "暂无专辑",
        }));
        var __VLS_43 = __VLS_42.apply(void 0, __spreadArray([{
                description: "暂无专辑",
            }], __VLS_functionalComponentArgsRest(__VLS_42), false));
    }
    else {
        var __VLS_46 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nGrid | typeof __VLS_components.NGrid | typeof __VLS_components.nGrid | typeof __VLS_components.NGrid} */
        nGrid;
        // @ts-ignore
        var __VLS_47 = __VLS_asFunctionalComponent1(__VLS_46, new __VLS_46({
            xGap: "16",
            yGap: "16",
            cols: (__VLS_ctx.responsiveCols),
        }));
        var __VLS_48 = __VLS_47.apply(void 0, __spreadArray([{
                xGap: "16",
                yGap: "16",
                cols: (__VLS_ctx.responsiveCols),
            }], __VLS_functionalComponentArgsRest(__VLS_47), false));
        var __VLS_51 = __VLS_49.slots.default;
        var _loop_1 = function (album) {
            var __VLS_52 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nGridItem | typeof __VLS_components.NGridItem | typeof __VLS_components.nGridItem | typeof __VLS_components.NGridItem} */
            nGridItem;
            // @ts-ignore
            var __VLS_53 = __VLS_asFunctionalComponent1(__VLS_52, new __VLS_52({
                key: (album.id),
            }));
            var __VLS_54 = __VLS_53.apply(void 0, __spreadArray([{
                    key: (album.id),
                }], __VLS_functionalComponentArgsRest(__VLS_53), false));
            var __VLS_57 = __VLS_55.slots.default;
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ onClick: function () {
                    var _a = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        _a[_i] = arguments[_i];
                    }
                    var $event = _a[0];
                    if (!!(!__VLS_ctx.loading && !__VLS_ctx.artist))
                        return;
                    if (!(__VLS_ctx.artist))
                        return;
                    if (!!(!__VLS_ctx.albumsLoading && !__VLS_ctx.albums.length))
                        return;
                    __VLS_ctx.goToAlbum(album.id);
                    // @ts-ignore
                    [albumsLoading, albumsLoading, albums, albums, responsiveCols, goToAlbum,];
                } }, { class: "album-item" }));
            /** @type {__VLS_StyleScopedClasses['album-item']} */ ;
            var __VLS_58 = AlbumCover_vue_1.default;
            // @ts-ignore
            var __VLS_59 = __VLS_asFunctionalComponent1(__VLS_58, new __VLS_58({
                coverUrl: (album.cover_url),
                title: (album.title),
            }));
            var __VLS_60 = __VLS_59.apply(void 0, __spreadArray([{
                    coverUrl: (album.cover_url),
                    title: (album.title),
                }], __VLS_functionalComponentArgsRest(__VLS_59), false));
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "album-info" }));
            /** @type {__VLS_StyleScopedClasses['album-info']} */ ;
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "album-title" }));
            /** @type {__VLS_StyleScopedClasses['album-title']} */ ;
            (album.title);
            __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "album-year" }));
            /** @type {__VLS_StyleScopedClasses['album-year']} */ ;
            ((_a = album.release_date) === null || _a === void 0 ? void 0 : _a.substring(0, 4));
            // @ts-ignore
            [];
            // @ts-ignore
            [];
        };
        var __VLS_55;
        for (var _c = 0, _d = __VLS_vFor((__VLS_ctx.albums)); _c < _d.length; _c++) {
            var album = _d[_c][0];
            _loop_1(album);
        }
        // @ts-ignore
        [];
        var __VLS_49;
    }
    // @ts-ignore
    [];
    var __VLS_38;
    // @ts-ignore
    [];
    var __VLS_32;
    var __VLS_63 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
    nCard;
    // @ts-ignore
    var __VLS_64 = __VLS_asFunctionalComponent1(__VLS_63, new __VLS_63(__assign({ title: "热门曲目" }, { style: {} })));
    var __VLS_65 = __VLS_64.apply(void 0, __spreadArray([__assign({ title: "热门曲目" }, { style: {} })], __VLS_functionalComponentArgsRest(__VLS_64), false));
    var __VLS_68 = __VLS_66.slots.default;
    var __VLS_69 = Loading_vue_1.default || Loading_vue_1.default;
    // @ts-ignore
    var __VLS_70 = __VLS_asFunctionalComponent1(__VLS_69, new __VLS_69({
        loading: (__VLS_ctx.tracksLoading),
        description: "加载曲目中...",
    }));
    var __VLS_71 = __VLS_70.apply(void 0, __spreadArray([{
            loading: (__VLS_ctx.tracksLoading),
            description: "加载曲目中...",
        }], __VLS_functionalComponentArgsRest(__VLS_70), false));
    var __VLS_74 = __VLS_72.slots.default;
    if (__VLS_ctx.tracks.length) {
        var __VLS_75 = TrackList_vue_1.default;
        // @ts-ignore
        var __VLS_76 = __VLS_asFunctionalComponent1(__VLS_75, new __VLS_75({
            tracks: (__VLS_ctx.tracks),
        }));
        var __VLS_77 = __VLS_76.apply(void 0, __spreadArray([{
                tracks: (__VLS_ctx.tracks),
            }], __VLS_functionalComponentArgsRest(__VLS_76), false));
    }
    // @ts-ignore
    [tracksLoading, tracks, tracks,];
    var __VLS_72;
    // @ts-ignore
    [];
    var __VLS_66;
}
// @ts-ignore
[];
var __VLS_10;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({});
exports.default = {};
