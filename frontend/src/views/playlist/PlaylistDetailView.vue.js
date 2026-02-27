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
var _a, _b, _c, _d, _e, _f;
Object.defineProperty(exports, "__esModule", { value: true });
var vue_1 = require("vue");
var vue_router_1 = require("vue-router");
var ionicons5_1 = require("@vicons/ionicons5");
var TrackList_vue_1 = require("@/components/audio/TrackList.vue");
var Loading_vue_1 = require("@/components/common/Loading.vue");
var player_1 = require("@/store/player");
var router = (0, vue_router_1.useRouter)();
var route = (0, vue_router_1.useRoute)();
var playerStore = (0, player_1.usePlayerStore)();
var loading = (0, vue_1.ref)(false);
var tracksLoading = (0, vue_1.ref)(false);
var playlist = (0, vue_1.ref)(null);
var tracks = (0, vue_1.ref)([]);
var dragMode = (0, vue_1.ref)(false);
var showAddTrackModal = (0, vue_1.ref)(false);
var addTrackForm = (0, vue_1.ref)({
    mode: 'track',
});
var addTrackRules = {};
var playlistId = (0, vue_1.computed)(function () { return Number(route.params.id); });
// 计算总时长
var totalDuration = (0, vue_1.computed)(function () {
    var totalMs = tracks.value.reduce(function (sum, track) { return sum + (track.duration || 0); }, 0);
    var totalSeconds = Math.floor(totalMs / 1000);
    var hours = Math.floor(totalSeconds / 3600);
    var mins = Math.floor((totalSeconds % 3600) / 60);
    if (hours > 0) {
        return "".concat(hours, ":").concat(mins.toString().padStart(2, '0'), ":00");
    }
    return "".concat(mins, ":00");
});
(0, vue_1.onMounted)(function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, loadPlaylist()];
            case 1:
                _a.sent();
                return [4 /*yield*/, loadTracks()];
            case 2:
                _a.sent();
                return [2 /*return*/];
        }
    });
}); });
function loadPlaylist() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            loading.value = true;
            try {
                // TODO: 调用 playlistApi.getById(playlistId.value)
                playlist.value = {
                    id: playlistId.value,
                    name: '示例播放列表',
                    type: 'normal',
                    description: '这是一个示例播放列表',
                };
            }
            finally {
                loading.value = false;
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
                // TODO: 调用 playlistApi.getTracks(playlistId.value)
                tracks.value = [
                    // 示例数据
                    { id: 1, title: '示例曲目 1', artist: '艺术家 A', album: '专辑 A', duration: 180000 },
                    { id: 2, title: '示例曲目 2', artist: '艺术家 B', album: '专辑 B', duration: 210000 },
                ];
            }
            finally {
                tracksLoading.value = false;
            }
            return [2 /*return*/];
        });
    });
}
function goBack() {
    router.back();
}
// 播放曲目
function handleTrackPlay(track) {
    // 设置播放队列并播放
    playerStore.setQueue(tracks.value, tracks.value.findIndex(function (t) { return t.id === track.id; }));
}
// 播放整个播放列表
function playPlaylist() {
    if (tracks.value.length === 0)
        return;
    playerStore.setQueue(tracks.value, 0);
    playerStore.playTrack(tracks.value[0]);
}
// 随机播放
function shufflePlay() {
    if (tracks.value.length === 0)
        return;
    var shuffled = __spreadArray([], tracks.value, true).sort(function () { return Math.random() - 0.5; });
    playerStore.setQueue(shuffled, 0);
    playerStore.setRepeatMode('all');
    playerStore.toggleShuffle();
    playerStore.playTrack(shuffled[0]);
}
// 切换拖拽排序模式
function toggleDragMode() {
    dragMode.value = !dragMode.value;
}
// 处理曲目重排序
function handleReorder(reorderedTracks) {
    tracks.value = reorderedTracks;
    // TODO: 调用 API 保存新顺序
}
// 移除曲目
function handleRemoveTracks(trackIds) {
    tracks.value = tracks.value.filter(function (t) { return !trackIds.includes(t.id); });
    // TODO: 调用 API 删除曲目
}
// 添加到队列
function handleAddToQueue(newTracks) {
    playerStore.addToQueue(newTracks);
}
// 刷新智能播放列表
function refreshSmartPlaylist() {
    // TODO: 调用 API 刷新智能播放列表
    loadTracks();
}
// 添加曲目
function handleAddTracks() {
    // TODO: 调用 API 添加曲目
    showAddTrackModal.value = false;
}
var __VLS_ctx = __assign(__assign({}, {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "playlist-detail-view" }));
/** @type {__VLS_StyleScopedClasses['playlist-detail-view']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader | typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader} */
nPageHeader;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0(__assign({ 'onBack': {} }, { title: (((_a = __VLS_ctx.playlist) === null || _a === void 0 ? void 0 : _a.name) || '播放列表详情') })));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([__assign({ 'onBack': {} }, { title: (((_b = __VLS_ctx.playlist) === null || _b === void 0 ? void 0 : _b.name) || '播放列表详情') })], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5;
var __VLS_6 = ({ back: {} },
    { onBack: (__VLS_ctx.goBack) });
var __VLS_7 = __VLS_3.slots.default;
{
    var __VLS_8 = __VLS_3.slots.extra;
    var __VLS_9 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
    nSpace;
    // @ts-ignore
    var __VLS_10 = __VLS_asFunctionalComponent1(__VLS_9, new __VLS_9({}));
    var __VLS_11 = __VLS_10.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_10), false));
    var __VLS_14 = __VLS_12.slots.default;
    if (((_c = __VLS_ctx.playlist) === null || _c === void 0 ? void 0 : _c.type) === 'smart') {
        var __VLS_15 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
        nButton;
        // @ts-ignore
        var __VLS_16 = __VLS_asFunctionalComponent1(__VLS_15, new __VLS_15(__assign({ 'onClick': {} }, { size: "small" })));
        var __VLS_17 = __VLS_16.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small" })], __VLS_functionalComponentArgsRest(__VLS_16), false));
        var __VLS_20 = void 0;
        var __VLS_21 = ({ click: {} },
            { onClick: (__VLS_ctx.refreshSmartPlaylist) });
        var __VLS_22 = __VLS_18.slots.default;
        {
            var __VLS_23 = __VLS_18.slots.icon;
            var __VLS_24 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
            nIcon;
            // @ts-ignore
            var __VLS_25 = __VLS_asFunctionalComponent1(__VLS_24, new __VLS_24({}));
            var __VLS_26 = __VLS_25.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_25), false));
            var __VLS_29 = __VLS_27.slots.default;
            var __VLS_30 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.RefreshIcon} */
            ionicons5_1.RefreshOutline;
            // @ts-ignore
            var __VLS_31 = __VLS_asFunctionalComponent1(__VLS_30, new __VLS_30({}));
            var __VLS_32 = __VLS_31.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_31), false));
            // @ts-ignore
            [playlist, playlist, goBack, refreshSmartPlaylist,];
            var __VLS_27;
            // @ts-ignore
            [];
        }
        // @ts-ignore
        [];
        var __VLS_18;
        var __VLS_19;
    }
    if (((_d = __VLS_ctx.playlist) === null || _d === void 0 ? void 0 : _d.type) === 'normal') {
        var __VLS_35 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
        nButton;
        // @ts-ignore
        var __VLS_36 = __VLS_asFunctionalComponent1(__VLS_35, new __VLS_35(__assign({ 'onClick': {} }, { size: "small" })));
        var __VLS_37 = __VLS_36.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small" })], __VLS_functionalComponentArgsRest(__VLS_36), false));
        var __VLS_40 = void 0;
        var __VLS_41 = ({ click: {} },
            { onClick: function () {
                    var _a;
                    var _b = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        _b[_i] = arguments[_i];
                    }
                    var $event = _b[0];
                    if (!(((_a = __VLS_ctx.playlist) === null || _a === void 0 ? void 0 : _a.type) === 'normal'))
                        return;
                    __VLS_ctx.showAddTrackModal = true;
                    // @ts-ignore
                    [playlist, showAddTrackModal,];
                } });
        var __VLS_42 = __VLS_38.slots.default;
        {
            var __VLS_43 = __VLS_38.slots.icon;
            var __VLS_44 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
            nIcon;
            // @ts-ignore
            var __VLS_45 = __VLS_asFunctionalComponent1(__VLS_44, new __VLS_44({}));
            var __VLS_46 = __VLS_45.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_45), false));
            var __VLS_49 = __VLS_47.slots.default;
            var __VLS_50 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.AddIcon} */
            ionicons5_1.AddOutline;
            // @ts-ignore
            var __VLS_51 = __VLS_asFunctionalComponent1(__VLS_50, new __VLS_50({}));
            var __VLS_52 = __VLS_51.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_51), false));
            // @ts-ignore
            [];
            var __VLS_47;
            // @ts-ignore
            [];
        }
        // @ts-ignore
        [];
        var __VLS_38;
        var __VLS_39;
    }
    var __VLS_55 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_56 = __VLS_asFunctionalComponent1(__VLS_55, new __VLS_55(__assign({ 'onClick': {} }, { size: "small" })));
    var __VLS_57 = __VLS_56.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small" })], __VLS_functionalComponentArgsRest(__VLS_56), false));
    var __VLS_60 = void 0;
    var __VLS_61 = ({ click: {} },
        { onClick: (__VLS_ctx.playPlaylist) });
    var __VLS_62 = __VLS_58.slots.default;
    {
        var __VLS_63 = __VLS_58.slots.icon;
        var __VLS_64 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
        nIcon;
        // @ts-ignore
        var __VLS_65 = __VLS_asFunctionalComponent1(__VLS_64, new __VLS_64({}));
        var __VLS_66 = __VLS_65.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_65), false));
        var __VLS_69 = __VLS_67.slots.default;
        var __VLS_70 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.PlayIcon} */
        ionicons5_1.PlayOutline;
        // @ts-ignore
        var __VLS_71 = __VLS_asFunctionalComponent1(__VLS_70, new __VLS_70({}));
        var __VLS_72 = __VLS_71.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_71), false));
        // @ts-ignore
        [playPlaylist,];
        var __VLS_67;
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_58;
    var __VLS_59;
    // @ts-ignore
    [];
    var __VLS_12;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_3;
var __VLS_4;
var __VLS_75 = Loading_vue_1.default || Loading_vue_1.default;
// @ts-ignore
var __VLS_76 = __VLS_asFunctionalComponent1(__VLS_75, new __VLS_75({
    loading: (__VLS_ctx.loading),
    description: "加载中...",
}));
var __VLS_77 = __VLS_76.apply(void 0, __spreadArray([{
        loading: (__VLS_ctx.loading),
        description: "加载中...",
    }], __VLS_functionalComponentArgsRest(__VLS_76), false));
var __VLS_80 = __VLS_78.slots.default;
if (!__VLS_ctx.loading && !__VLS_ctx.playlist) {
    var __VLS_81 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
    nEmpty;
    // @ts-ignore
    var __VLS_82 = __VLS_asFunctionalComponent1(__VLS_81, new __VLS_81({
        description: "播放列表不存在",
    }));
    var __VLS_83 = __VLS_82.apply(void 0, __spreadArray([{
            description: "播放列表不存在",
        }], __VLS_functionalComponentArgsRest(__VLS_82), false));
}
else if (__VLS_ctx.playlist) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    if (__VLS_ctx.playlist.description) {
        var __VLS_86 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
        nCard;
        // @ts-ignore
        var __VLS_87 = __VLS_asFunctionalComponent1(__VLS_86, new __VLS_86(__assign({ style: {} })));
        var __VLS_88 = __VLS_87.apply(void 0, __spreadArray([__assign({ style: {} })], __VLS_functionalComponentArgsRest(__VLS_87), false));
        var __VLS_91 = __VLS_89.slots.default;
        __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
        (__VLS_ctx.playlist.description);
        // @ts-ignore
        [playlist, playlist, playlist, playlist, loading, loading,];
        var __VLS_89;
    }
    var __VLS_92 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
    nCard;
    // @ts-ignore
    var __VLS_93 = __VLS_asFunctionalComponent1(__VLS_92, new __VLS_92({}));
    var __VLS_94 = __VLS_93.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_93), false));
    var __VLS_97 = __VLS_95.slots.default;
    {
        var __VLS_98 = __VLS_95.slots.header;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ style: {} }));
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (__VLS_ctx.tracks.length);
        var __VLS_99 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
        nSpace;
        // @ts-ignore
        var __VLS_100 = __VLS_asFunctionalComponent1(__VLS_99, new __VLS_99({}));
        var __VLS_101 = __VLS_100.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_100), false));
        var __VLS_104 = __VLS_102.slots.default;
        if (((_e = __VLS_ctx.playlist) === null || _e === void 0 ? void 0 : _e.type) === 'normal') {
            var __VLS_105 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
            nButton;
            // @ts-ignore
            var __VLS_106 = __VLS_asFunctionalComponent1(__VLS_105, new __VLS_105(__assign({ 'onClick': {} }, { size: "small", quaternary: true })));
            var __VLS_107 = __VLS_106.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small", quaternary: true })], __VLS_functionalComponentArgsRest(__VLS_106), false));
            var __VLS_110 = void 0;
            var __VLS_111 = ({ click: {} },
                { onClick: (__VLS_ctx.toggleDragMode) });
            var __VLS_112 = __VLS_108.slots.default;
            {
                var __VLS_113 = __VLS_108.slots.icon;
                var __VLS_114 = void 0;
                /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
                nIcon;
                // @ts-ignore
                var __VLS_115 = __VLS_asFunctionalComponent1(__VLS_114, new __VLS_114({}));
                var __VLS_116 = __VLS_115.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_115), false));
                var __VLS_119 = __VLS_117.slots.default;
                var __VLS_120 = void 0;
                /** @ts-ignore @type {typeof __VLS_components.MenuIcon} */
                ionicons5_1.Menu;
                // @ts-ignore
                var __VLS_121 = __VLS_asFunctionalComponent1(__VLS_120, new __VLS_120({}));
                var __VLS_122 = __VLS_121.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_121), false));
                // @ts-ignore
                [playlist, tracks, toggleDragMode,];
                var __VLS_117;
                // @ts-ignore
                [];
            }
            (__VLS_ctx.dragMode ? '完成排序' : '排序');
            // @ts-ignore
            [dragMode,];
            var __VLS_108;
            var __VLS_109;
        }
        var __VLS_125 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
        nButton;
        // @ts-ignore
        var __VLS_126 = __VLS_asFunctionalComponent1(__VLS_125, new __VLS_125(__assign({ 'onClick': {} }, { size: "small", quaternary: true })));
        var __VLS_127 = __VLS_126.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small", quaternary: true })], __VLS_functionalComponentArgsRest(__VLS_126), false));
        var __VLS_130 = void 0;
        var __VLS_131 = ({ click: {} },
            { onClick: (__VLS_ctx.shufflePlay) });
        var __VLS_132 = __VLS_128.slots.default;
        {
            var __VLS_133 = __VLS_128.slots.icon;
            var __VLS_134 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
            nIcon;
            // @ts-ignore
            var __VLS_135 = __VLS_asFunctionalComponent1(__VLS_134, new __VLS_134({}));
            var __VLS_136 = __VLS_135.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_135), false));
            var __VLS_139 = __VLS_137.slots.default;
            var __VLS_140 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.ShuffleIcon} */
            ionicons5_1.ShuffleOutline;
            // @ts-ignore
            var __VLS_141 = __VLS_asFunctionalComponent1(__VLS_140, new __VLS_140({}));
            var __VLS_142 = __VLS_141.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_141), false));
            // @ts-ignore
            [shufflePlay,];
            var __VLS_137;
            // @ts-ignore
            [];
        }
        // @ts-ignore
        [];
        var __VLS_128;
        var __VLS_129;
        // @ts-ignore
        [];
        var __VLS_102;
        // @ts-ignore
        [];
    }
    var __VLS_145 = Loading_vue_1.default || Loading_vue_1.default;
    // @ts-ignore
    var __VLS_146 = __VLS_asFunctionalComponent1(__VLS_145, new __VLS_145({
        loading: (__VLS_ctx.tracksLoading),
        description: "加载曲目中...",
    }));
    var __VLS_147 = __VLS_146.apply(void 0, __spreadArray([{
            loading: (__VLS_ctx.tracksLoading),
            description: "加载曲目中...",
        }], __VLS_functionalComponentArgsRest(__VLS_146), false));
    var __VLS_150 = __VLS_148.slots.default;
    if (!__VLS_ctx.tracksLoading && !__VLS_ctx.tracks.length) {
        var __VLS_151 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
        nEmpty;
        // @ts-ignore
        var __VLS_152 = __VLS_asFunctionalComponent1(__VLS_151, new __VLS_151({
            description: "暂无曲目",
        }));
        var __VLS_153 = __VLS_152.apply(void 0, __spreadArray([{
                description: "暂无曲目",
            }], __VLS_functionalComponentArgsRest(__VLS_152), false));
    }
    else {
        var __VLS_156 = TrackList_vue_1.default;
        // @ts-ignore
        var __VLS_157 = __VLS_asFunctionalComponent1(__VLS_156, new __VLS_156(__assign(__assign(__assign(__assign({ 'onPlay': {} }, { 'onReorder': {} }), { 'onRemove': {} }), { 'onAddToQueue': {} }), { tracks: (__VLS_ctx.tracks), draggable: (__VLS_ctx.dragMode), selectable: (true), showBatchActions: (true) })));
        var __VLS_158 = __VLS_157.apply(void 0, __spreadArray([__assign(__assign(__assign(__assign({ 'onPlay': {} }, { 'onReorder': {} }), { 'onRemove': {} }), { 'onAddToQueue': {} }), { tracks: (__VLS_ctx.tracks), draggable: (__VLS_ctx.dragMode), selectable: (true), showBatchActions: (true) })], __VLS_functionalComponentArgsRest(__VLS_157), false));
        var __VLS_161 = void 0;
        var __VLS_162 = ({ play: {} },
            { onPlay: (__VLS_ctx.handleTrackPlay) });
        var __VLS_163 = ({ reorder: {} },
            { onReorder: (__VLS_ctx.handleReorder) });
        var __VLS_164 = ({ remove: {} },
            { onRemove: (__VLS_ctx.handleRemoveTracks) });
        var __VLS_165 = ({ addToQueue: {} },
            { onAddToQueue: (__VLS_ctx.handleAddToQueue) });
        var __VLS_159;
        var __VLS_160;
    }
    // @ts-ignore
    [tracks, tracks, dragMode, tracksLoading, tracksLoading, handleTrackPlay, handleReorder, handleRemoveTracks, handleAddToQueue,];
    var __VLS_148;
    // @ts-ignore
    [];
    var __VLS_95;
    var __VLS_166 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
    nCard;
    // @ts-ignore
    var __VLS_167 = __VLS_asFunctionalComponent1(__VLS_166, new __VLS_166(__assign({ style: {} })));
    var __VLS_168 = __VLS_167.apply(void 0, __spreadArray([__assign({ style: {} })], __VLS_functionalComponentArgsRest(__VLS_167), false));
    var __VLS_171 = __VLS_169.slots.default;
    var __VLS_172 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptions | typeof __VLS_components.NDescriptions | typeof __VLS_components.nDescriptions | typeof __VLS_components.NDescriptions} */
    nDescriptions;
    // @ts-ignore
    var __VLS_173 = __VLS_asFunctionalComponent1(__VLS_172, new __VLS_172({
        column: (3),
        bordered: true,
    }));
    var __VLS_174 = __VLS_173.apply(void 0, __spreadArray([{
            column: (3),
            bordered: true,
        }], __VLS_functionalComponentArgsRest(__VLS_173), false));
    var __VLS_177 = __VLS_175.slots.default;
    var __VLS_178 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_179 = __VLS_asFunctionalComponent1(__VLS_178, new __VLS_178({
        label: "曲目数量",
    }));
    var __VLS_180 = __VLS_179.apply(void 0, __spreadArray([{
            label: "曲目数量",
        }], __VLS_functionalComponentArgsRest(__VLS_179), false));
    var __VLS_183 = __VLS_181.slots.default;
    (__VLS_ctx.tracks.length);
    // @ts-ignore
    [tracks,];
    var __VLS_181;
    var __VLS_184 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_185 = __VLS_asFunctionalComponent1(__VLS_184, new __VLS_184({
        label: "总时长",
    }));
    var __VLS_186 = __VLS_185.apply(void 0, __spreadArray([{
            label: "总时长",
        }], __VLS_functionalComponentArgsRest(__VLS_185), false));
    var __VLS_189 = __VLS_187.slots.default;
    (__VLS_ctx.totalDuration);
    // @ts-ignore
    [totalDuration,];
    var __VLS_187;
    var __VLS_190 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_191 = __VLS_asFunctionalComponent1(__VLS_190, new __VLS_190({
        label: "类型",
    }));
    var __VLS_192 = __VLS_191.apply(void 0, __spreadArray([{
            label: "类型",
        }], __VLS_functionalComponentArgsRest(__VLS_191), false));
    var __VLS_195 = __VLS_193.slots.default;
    (((_f = __VLS_ctx.playlist) === null || _f === void 0 ? void 0 : _f.type) === 'smart' ? '智能播放列表' : '普通播放列表');
    // @ts-ignore
    [playlist,];
    var __VLS_193;
    // @ts-ignore
    [];
    var __VLS_175;
    // @ts-ignore
    [];
    var __VLS_169;
}
// @ts-ignore
[];
var __VLS_78;
var __VLS_196;
/** @ts-ignore @type {typeof __VLS_components.nModal | typeof __VLS_components.NModal | typeof __VLS_components.nModal | typeof __VLS_components.NModal} */
nModal;
// @ts-ignore
var __VLS_197 = __VLS_asFunctionalComponent1(__VLS_196, new __VLS_196({
    show: (__VLS_ctx.showAddTrackModal),
    preset: "dialog",
    title: "添加曲目",
}));
var __VLS_198 = __VLS_197.apply(void 0, __spreadArray([{
        show: (__VLS_ctx.showAddTrackModal),
        preset: "dialog",
        title: "添加曲目",
    }], __VLS_functionalComponentArgsRest(__VLS_197), false));
var __VLS_201 = __VLS_199.slots.default;
var __VLS_202;
/** @ts-ignore @type {typeof __VLS_components.nForm | typeof __VLS_components.NForm | typeof __VLS_components.nForm | typeof __VLS_components.NForm} */
nForm;
// @ts-ignore
var __VLS_203 = __VLS_asFunctionalComponent1(__VLS_202, new __VLS_202({
    ref: "addTrackFormRef",
    model: (__VLS_ctx.addTrackForm),
    rules: (__VLS_ctx.addTrackRules),
}));
var __VLS_204 = __VLS_203.apply(void 0, __spreadArray([{
        ref: "addTrackFormRef",
        model: (__VLS_ctx.addTrackForm),
        rules: (__VLS_ctx.addTrackRules),
    }], __VLS_functionalComponentArgsRest(__VLS_203), false));
var __VLS_207 = {};
var __VLS_209 = __VLS_205.slots.default;
var __VLS_210;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_211 = __VLS_asFunctionalComponent1(__VLS_210, new __VLS_210({
    label: "选择方式",
    path: "mode",
}));
var __VLS_212 = __VLS_211.apply(void 0, __spreadArray([{
        label: "选择方式",
        path: "mode",
    }], __VLS_functionalComponentArgsRest(__VLS_211), false));
var __VLS_215 = __VLS_213.slots.default;
var __VLS_216;
/** @ts-ignore @type {typeof __VLS_components.nRadioGroup | typeof __VLS_components.NRadioGroup | typeof __VLS_components.nRadioGroup | typeof __VLS_components.NRadioGroup} */
nRadioGroup;
// @ts-ignore
var __VLS_217 = __VLS_asFunctionalComponent1(__VLS_216, new __VLS_216({
    value: (__VLS_ctx.addTrackForm.mode),
}));
var __VLS_218 = __VLS_217.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.addTrackForm.mode),
    }], __VLS_functionalComponentArgsRest(__VLS_217), false));
var __VLS_221 = __VLS_219.slots.default;
var __VLS_222;
/** @ts-ignore @type {typeof __VLS_components.nRadio | typeof __VLS_components.NRadio | typeof __VLS_components.nRadio | typeof __VLS_components.NRadio} */
nRadio;
// @ts-ignore
var __VLS_223 = __VLS_asFunctionalComponent1(__VLS_222, new __VLS_222({
    value: "artist",
}));
var __VLS_224 = __VLS_223.apply(void 0, __spreadArray([{
        value: "artist",
    }], __VLS_functionalComponentArgsRest(__VLS_223), false));
var __VLS_227 = __VLS_225.slots.default;
// @ts-ignore
[showAddTrackModal, addTrackForm, addTrackForm, addTrackRules,];
var __VLS_225;
var __VLS_228;
/** @ts-ignore @type {typeof __VLS_components.nRadio | typeof __VLS_components.NRadio | typeof __VLS_components.nRadio | typeof __VLS_components.NRadio} */
nRadio;
// @ts-ignore
var __VLS_229 = __VLS_asFunctionalComponent1(__VLS_228, new __VLS_228({
    value: "album",
}));
var __VLS_230 = __VLS_229.apply(void 0, __spreadArray([{
        value: "album",
    }], __VLS_functionalComponentArgsRest(__VLS_229), false));
var __VLS_233 = __VLS_231.slots.default;
// @ts-ignore
[];
var __VLS_231;
var __VLS_234;
/** @ts-ignore @type {typeof __VLS_components.nRadio | typeof __VLS_components.NRadio | typeof __VLS_components.nRadio | typeof __VLS_components.NRadio} */
nRadio;
// @ts-ignore
var __VLS_235 = __VLS_asFunctionalComponent1(__VLS_234, new __VLS_234({
    value: "track",
}));
var __VLS_236 = __VLS_235.apply(void 0, __spreadArray([{
        value: "track",
    }], __VLS_functionalComponentArgsRest(__VLS_235), false));
var __VLS_239 = __VLS_237.slots.default;
// @ts-ignore
[];
var __VLS_237;
// @ts-ignore
[];
var __VLS_219;
// @ts-ignore
[];
var __VLS_213;
// @ts-ignore
[];
var __VLS_205;
{
    var __VLS_240 = __VLS_199.slots.action;
    var __VLS_241 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_242 = __VLS_asFunctionalComponent1(__VLS_241, new __VLS_241(__assign({ 'onClick': {} })));
    var __VLS_243 = __VLS_242.apply(void 0, __spreadArray([__assign({ 'onClick': {} })], __VLS_functionalComponentArgsRest(__VLS_242), false));
    var __VLS_246 = void 0;
    var __VLS_247 = ({ click: {} },
        { onClick: function () {
                var _a = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    _a[_i] = arguments[_i];
                }
                var $event = _a[0];
                __VLS_ctx.showAddTrackModal = false;
                // @ts-ignore
                [showAddTrackModal,];
            } });
    var __VLS_248 = __VLS_244.slots.default;
    // @ts-ignore
    [];
    var __VLS_244;
    var __VLS_245;
    var __VLS_249 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_250 = __VLS_asFunctionalComponent1(__VLS_249, new __VLS_249(__assign({ 'onClick': {} }, { type: "primary" })));
    var __VLS_251 = __VLS_250.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary" })], __VLS_functionalComponentArgsRest(__VLS_250), false));
    var __VLS_254 = void 0;
    var __VLS_255 = ({ click: {} },
        { onClick: (__VLS_ctx.handleAddTracks) });
    var __VLS_256 = __VLS_252.slots.default;
    // @ts-ignore
    [handleAddTracks,];
    var __VLS_252;
    var __VLS_253;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_199;
// @ts-ignore
var __VLS_208 = __VLS_207;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({});
exports.default = {};
