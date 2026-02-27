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
var _a, _b;
Object.defineProperty(exports, "__esModule", { value: true });
var vue_1 = require("vue");
var vue_router_1 = require("vue-router");
var ionicons5_1 = require("@vicons/ionicons5");
var TrackList_vue_1 = require("@/components/audio/TrackList.vue");
var Pagination_vue_1 = require("@/components/common/Pagination.vue");
var Loading_vue_1 = require("@/components/common/Loading.vue");
var router = (0, vue_router_1.useRouter)();
var route = (0, vue_router_1.useRoute)();
var loading = (0, vue_1.ref)(false);
var scanning = (0, vue_1.ref)(false);
var library = (0, vue_1.ref)(null);
var tracksLoading = (0, vue_1.ref)(false);
var tracks = (0, vue_1.ref)([]);
var currentPage = (0, vue_1.ref)(1);
var pageSize = (0, vue_1.ref)(20);
var totalTracks = (0, vue_1.ref)(0);
var libraryId = (0, vue_1.computed)(function () { return Number(route.params.id); });
(0, vue_1.onMounted)(function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, loadLibrary()];
            case 1:
                _a.sent();
                return [4 /*yield*/, loadTracks()];
            case 2:
                _a.sent();
                return [2 /*return*/];
        }
    });
}); });
function loadLibrary() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            loading.value = true;
            try {
                // TODO: 调用 libraryApi.getById(libraryId.value)
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
                // TODO: 调用 trackApi.getByLibrary()
            }
            finally {
                tracksLoading.value = false;
            }
            return [2 /*return*/];
        });
    });
}
function handleScan() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    scanning.value = true;
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, , 2, 5]);
                    return [3 /*break*/, 5];
                case 2:
                    scanning.value = false;
                    return [4 /*yield*/, loadLibrary()];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, loadTracks()];
                case 4:
                    _a.sent();
                    return [7 /*endfinally*/];
                case 5: return [2 /*return*/];
            }
        });
    });
}
function goBack() {
    router.back();
}
var __VLS_ctx = __assign(__assign({}, {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "library-detail-view" }));
/** @type {__VLS_StyleScopedClasses['library-detail-view']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader} */
nPageHeader;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0(__assign({ 'onBack': {} }, { title: (((_a = __VLS_ctx.library) === null || _a === void 0 ? void 0 : _a.name) || '音乐库详情') })));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([__assign({ 'onBack': {} }, { title: (((_b = __VLS_ctx.library) === null || _b === void 0 ? void 0 : _b.name) || '音乐库详情') })], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5;
var __VLS_6 = ({ back: {} },
    { onBack: (__VLS_ctx.goBack) });
var __VLS_3;
var __VLS_4;
var __VLS_7;
/** @ts-ignore @type {typeof __VLS_components.nSpin | typeof __VLS_components.NSpin | typeof __VLS_components.nSpin | typeof __VLS_components.NSpin} */
nSpin;
// @ts-ignore
var __VLS_8 = __VLS_asFunctionalComponent1(__VLS_7, new __VLS_7({
    show: (__VLS_ctx.loading),
}));
var __VLS_9 = __VLS_8.apply(void 0, __spreadArray([{
        show: (__VLS_ctx.loading),
    }], __VLS_functionalComponentArgsRest(__VLS_8), false));
var __VLS_12 = __VLS_10.slots.default;
if (!__VLS_ctx.loading && !__VLS_ctx.library) {
    var __VLS_13 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
    nEmpty;
    // @ts-ignore
    var __VLS_14 = __VLS_asFunctionalComponent1(__VLS_13, new __VLS_13({
        description: "音乐库不存在",
    }));
    var __VLS_15 = __VLS_14.apply(void 0, __spreadArray([{
            description: "音乐库不存在",
        }], __VLS_functionalComponentArgsRest(__VLS_14), false));
}
else if (__VLS_ctx.library) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "library-detail" }));
    /** @type {__VLS_StyleScopedClasses['library-detail']} */ ;
    var __VLS_18 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
    nCard;
    // @ts-ignore
    var __VLS_19 = __VLS_asFunctionalComponent1(__VLS_18, new __VLS_18({
        title: (__VLS_ctx.library.name),
    }));
    var __VLS_20 = __VLS_19.apply(void 0, __spreadArray([{
            title: (__VLS_ctx.library.name),
        }], __VLS_functionalComponentArgsRest(__VLS_19), false));
    var __VLS_23 = __VLS_21.slots.default;
    var __VLS_24 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptions | typeof __VLS_components.NDescriptions | typeof __VLS_components.nDescriptions | typeof __VLS_components.NDescriptions} */
    nDescriptions;
    // @ts-ignore
    var __VLS_25 = __VLS_asFunctionalComponent1(__VLS_24, new __VLS_24({
        column: (1),
    }));
    var __VLS_26 = __VLS_25.apply(void 0, __spreadArray([{
            column: (1),
        }], __VLS_functionalComponentArgsRest(__VLS_25), false));
    var __VLS_29 = __VLS_27.slots.default;
    var __VLS_30 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_31 = __VLS_asFunctionalComponent1(__VLS_30, new __VLS_30({
        label: "路径",
    }));
    var __VLS_32 = __VLS_31.apply(void 0, __spreadArray([{
            label: "路径",
        }], __VLS_functionalComponentArgsRest(__VLS_31), false));
    var __VLS_35 = __VLS_33.slots.default;
    (__VLS_ctx.library.path);
    // @ts-ignore
    [library, library, library, library, library, goBack, loading, loading,];
    var __VLS_33;
    var __VLS_36 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_37 = __VLS_asFunctionalComponent1(__VLS_36, new __VLS_36({
        label: "曲目",
    }));
    var __VLS_38 = __VLS_37.apply(void 0, __spreadArray([{
            label: "曲目",
        }], __VLS_functionalComponentArgsRest(__VLS_37), false));
    var __VLS_41 = __VLS_39.slots.default;
    (__VLS_ctx.library.trackCount || 0);
    // @ts-ignore
    [library,];
    var __VLS_39;
    var __VLS_42 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_43 = __VLS_asFunctionalComponent1(__VLS_42, new __VLS_42({
        label: "专辑",
    }));
    var __VLS_44 = __VLS_43.apply(void 0, __spreadArray([{
            label: "专辑",
        }], __VLS_functionalComponentArgsRest(__VLS_43), false));
    var __VLS_47 = __VLS_45.slots.default;
    (__VLS_ctx.library.albumCount || 0);
    // @ts-ignore
    [library,];
    var __VLS_45;
    var __VLS_48 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_49 = __VLS_asFunctionalComponent1(__VLS_48, new __VLS_48({
        label: "艺术家",
    }));
    var __VLS_50 = __VLS_49.apply(void 0, __spreadArray([{
            label: "艺术家",
        }], __VLS_functionalComponentArgsRest(__VLS_49), false));
    var __VLS_53 = __VLS_51.slots.default;
    (__VLS_ctx.library.artistCount || 0);
    // @ts-ignore
    [library,];
    var __VLS_51;
    var __VLS_54 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_55 = __VLS_asFunctionalComponent1(__VLS_54, new __VLS_54({
        label: "最后扫描",
    }));
    var __VLS_56 = __VLS_55.apply(void 0, __spreadArray([{
            label: "最后扫描",
        }], __VLS_functionalComponentArgsRest(__VLS_55), false));
    var __VLS_59 = __VLS_57.slots.default;
    (__VLS_ctx.library.lastScanTime || '未扫描');
    // @ts-ignore
    [library,];
    var __VLS_57;
    var __VLS_60 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem | typeof __VLS_components.nDescriptionsItem | typeof __VLS_components.NDescriptionsItem} */
    nDescriptionsItem;
    // @ts-ignore
    var __VLS_61 = __VLS_asFunctionalComponent1(__VLS_60, new __VLS_60({
        label: "自动扫描",
    }));
    var __VLS_62 = __VLS_61.apply(void 0, __spreadArray([{
            label: "自动扫描",
        }], __VLS_functionalComponentArgsRest(__VLS_61), false));
    var __VLS_65 = __VLS_63.slots.default;
    (__VLS_ctx.library.autoScan ? '开启' : '关闭');
    // @ts-ignore
    [library,];
    var __VLS_63;
    // @ts-ignore
    [];
    var __VLS_27;
    {
        var __VLS_66 = __VLS_21.slots.footer;
        var __VLS_67 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
        nSpace;
        // @ts-ignore
        var __VLS_68 = __VLS_asFunctionalComponent1(__VLS_67, new __VLS_67({}));
        var __VLS_69 = __VLS_68.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_68), false));
        var __VLS_72 = __VLS_70.slots.default;
        var __VLS_73 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
        nButton;
        // @ts-ignore
        var __VLS_74 = __VLS_asFunctionalComponent1(__VLS_73, new __VLS_73(__assign({ 'onClick': {} }, { type: "primary", loading: (__VLS_ctx.scanning) })));
        var __VLS_75 = __VLS_74.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary", loading: (__VLS_ctx.scanning) })], __VLS_functionalComponentArgsRest(__VLS_74), false));
        var __VLS_78 = void 0;
        var __VLS_79 = ({ click: {} },
            { onClick: (__VLS_ctx.handleScan) });
        var __VLS_80 = __VLS_76.slots.default;
        {
            var __VLS_81 = __VLS_76.slots.icon;
            var __VLS_82 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
            nIcon;
            // @ts-ignore
            var __VLS_83 = __VLS_asFunctionalComponent1(__VLS_82, new __VLS_82({}));
            var __VLS_84 = __VLS_83.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_83), false));
            var __VLS_87 = __VLS_85.slots.default;
            var __VLS_88 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.RefreshIcon} */
            ionicons5_1.RefreshOutline;
            // @ts-ignore
            var __VLS_89 = __VLS_asFunctionalComponent1(__VLS_88, new __VLS_88({}));
            var __VLS_90 = __VLS_89.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_89), false));
            // @ts-ignore
            [scanning, handleScan,];
            var __VLS_85;
            // @ts-ignore
            [];
        }
        // @ts-ignore
        [];
        var __VLS_76;
        var __VLS_77;
        // @ts-ignore
        [];
        var __VLS_70;
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_21;
    var __VLS_93 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
    nCard;
    // @ts-ignore
    var __VLS_94 = __VLS_asFunctionalComponent1(__VLS_93, new __VLS_93(__assign({ title: "曲目列表" }, { style: {} })));
    var __VLS_95 = __VLS_94.apply(void 0, __spreadArray([__assign({ title: "曲目列表" }, { style: {} })], __VLS_functionalComponentArgsRest(__VLS_94), false));
    var __VLS_98 = __VLS_96.slots.default;
    var __VLS_99 = Loading_vue_1.default || Loading_vue_1.default;
    // @ts-ignore
    var __VLS_100 = __VLS_asFunctionalComponent1(__VLS_99, new __VLS_99({
        loading: (__VLS_ctx.tracksLoading),
        description: "加载曲目中...",
    }));
    var __VLS_101 = __VLS_100.apply(void 0, __spreadArray([{
            loading: (__VLS_ctx.tracksLoading),
            description: "加载曲目中...",
        }], __VLS_functionalComponentArgsRest(__VLS_100), false));
    var __VLS_104 = __VLS_102.slots.default;
    if (!__VLS_ctx.tracksLoading && !__VLS_ctx.tracks.length) {
        var __VLS_105 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
        nEmpty;
        // @ts-ignore
        var __VLS_106 = __VLS_asFunctionalComponent1(__VLS_105, new __VLS_105({
            description: "暂无曲目",
        }));
        var __VLS_107 = __VLS_106.apply(void 0, __spreadArray([{
                description: "暂无曲目",
            }], __VLS_functionalComponentArgsRest(__VLS_106), false));
    }
    else {
        var __VLS_110 = TrackList_vue_1.default;
        // @ts-ignore
        var __VLS_111 = __VLS_asFunctionalComponent1(__VLS_110, new __VLS_110({
            tracks: (__VLS_ctx.tracks),
        }));
        var __VLS_112 = __VLS_111.apply(void 0, __spreadArray([{
                tracks: (__VLS_ctx.tracks),
            }], __VLS_functionalComponentArgsRest(__VLS_111), false));
    }
    if (__VLS_ctx.tracks.length) {
        var __VLS_115 = Pagination_vue_1.default;
        // @ts-ignore
        var __VLS_116 = __VLS_asFunctionalComponent1(__VLS_115, new __VLS_115({
            page: (__VLS_ctx.currentPage),
            pageSize: (__VLS_ctx.pageSize),
            totalItems: (__VLS_ctx.totalTracks),
        }));
        var __VLS_117 = __VLS_116.apply(void 0, __spreadArray([{
                page: (__VLS_ctx.currentPage),
                pageSize: (__VLS_ctx.pageSize),
                totalItems: (__VLS_ctx.totalTracks),
            }], __VLS_functionalComponentArgsRest(__VLS_116), false));
    }
    // @ts-ignore
    [tracksLoading, tracksLoading, tracks, tracks, tracks, currentPage, pageSize, totalTracks,];
    var __VLS_102;
    // @ts-ignore
    [];
    var __VLS_96;
}
// @ts-ignore
[];
var __VLS_10;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({});
exports.default = {};
