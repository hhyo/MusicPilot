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
Object.defineProperty(exports, "__esModule", { value: true });
var vue_1 = require("vue");
var naive_ui_1 = require("naive-ui");
var ionicons5_1 = require("@vicons/ionicons5");
var subscribeApi = require("@/api/subscribe");
var props = defineProps();
var __VLS_emit = defineEmits();
var message = (0, naive_ui_1.useMessage)();
var loading = (0, vue_1.ref)(false);
var emptyDescription = (0, vue_1.computed)(function () {
    switch (props.type) {
        case 'artist':
            return '暂无艺术家订阅';
        case 'album':
            return '暂无专辑订阅';
        case 'playlist':
            return '暂无歌单订阅';
        case 'chart':
            return '暂无榜单订阅';
        default:
            return '暂无订阅';
    }
});
var getIcon = function () {
    switch (props.type) {
        case 'artist':
            return ionicons5_1.PersonOutline;
        case 'album':
            return ionicons5_1.AlbumOutline;
        case 'playlist':
            return ionicons5_1.MusicalNotesOutline;
        case 'chart':
            return ionicons5_1.RibbonOutline;
        default:
            return ionicons5_1.MusicalNotesOutline;
    }
};
var getIconColor = function () {
    switch (props.type) {
        case 'artist':
            return '#18a058';
        case 'album':
            return '#2080f0';
        case 'playlist':
            return '#f0a020';
        case 'chart':
            return '#d03050';
        default:
            return '#909399';
    }
};
var toggleState = function (subscribe) { return __awaiter(void 0, void 0, void 0, function () {
    var newState, action, error_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                newState = subscribe.state === 'paused' ? 'active' : 'paused';
                action = newState === 'active' ? '启用' : '暂停';
                _a.label = 1;
            case 1:
                _a.trys.push([1, 3, , 4]);
                return [4 /*yield*/, subscribeApi.updateSubscribe(subscribe.id, { state: newState })];
            case 2:
                _a.sent();
                message.success("".concat(action, "\u6210\u529F"));
                emit('refresh');
                return [3 /*break*/, 4];
            case 3:
                error_1 = _a.sent();
                message.error("".concat(action, "\u5931\u8D25"));
                return [3 /*break*/, 4];
            case 4: return [2 /*return*/];
        }
    });
}); };
var __VLS_ctx = __assign(__assign(__assign(__assign(__assign({}, {}), {}), {}), {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "subscribe-list" }));
/** @type {__VLS_StyleScopedClasses['subscribe-list']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
nSpace;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    vertical: true,
}));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([{
        vertical: true,
    }], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5 = __VLS_3.slots.default;
var __VLS_6;
/** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
nSpace;
// @ts-ignore
var __VLS_7 = __VLS_asFunctionalComponent1(__VLS_6, new __VLS_6({
    justify: "space-between",
}));
var __VLS_8 = __VLS_7.apply(void 0, __spreadArray([{
        justify: "space-between",
    }], __VLS_functionalComponentArgsRest(__VLS_7), false));
var __VLS_11 = __VLS_9.slots.default;
var __VLS_12;
/** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
nSpace;
// @ts-ignore
var __VLS_13 = __VLS_asFunctionalComponent1(__VLS_12, new __VLS_12({}));
var __VLS_14 = __VLS_13.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_13), false));
var __VLS_17 = __VLS_15.slots.default;
var __VLS_18;
/** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
nButton;
// @ts-ignore
var __VLS_19 = __VLS_asFunctionalComponent1(__VLS_18, new __VLS_18(__assign({ 'onClick': {} }, { quaternary: true })));
var __VLS_20 = __VLS_19.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { quaternary: true })], __VLS_functionalComponentArgsRest(__VLS_19), false));
var __VLS_23;
var __VLS_24 = ({ click: {} },
    { onClick: function () {
            var _a = [];
            for (var _i = 0; _i < arguments.length; _i++) {
                _a[_i] = arguments[_i];
            }
            var $event = _a[0];
            __VLS_ctx.$emit('refresh');
            // @ts-ignore
            [$emit,];
        } });
var __VLS_25 = __VLS_21.slots.default;
{
    var __VLS_26 = __VLS_21.slots.icon;
    var __VLS_27 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
    nIcon;
    // @ts-ignore
    var __VLS_28 = __VLS_asFunctionalComponent1(__VLS_27, new __VLS_27({}));
    var __VLS_29 = __VLS_28.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_28), false));
    var __VLS_32 = __VLS_30.slots.default;
    var __VLS_33 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.RefreshIcon} */
    ionicons5_1.RefreshOutline;
    // @ts-ignore
    var __VLS_34 = __VLS_asFunctionalComponent1(__VLS_33, new __VLS_33({}));
    var __VLS_35 = __VLS_34.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_34), false));
    // @ts-ignore
    [];
    var __VLS_30;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_21;
var __VLS_22;
// @ts-ignore
[];
var __VLS_15;
if (__VLS_ctx.subscribes.length > 0) {
    var __VLS_38 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
    nSpace;
    // @ts-ignore
    var __VLS_39 = __VLS_asFunctionalComponent1(__VLS_38, new __VLS_38({}));
    var __VLS_40 = __VLS_39.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_39), false));
    var __VLS_43 = __VLS_41.slots.default;
    var __VLS_44 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nText | typeof __VLS_components.NText | typeof __VLS_components.nText | typeof __VLS_components.NText} */
    nText;
    // @ts-ignore
    var __VLS_45 = __VLS_asFunctionalComponent1(__VLS_44, new __VLS_44({
        depth: "3",
    }));
    var __VLS_46 = __VLS_45.apply(void 0, __spreadArray([{
            depth: "3",
        }], __VLS_functionalComponentArgsRest(__VLS_45), false));
    var __VLS_49 = __VLS_47.slots.default;
    (__VLS_ctx.subscribes.length);
    // @ts-ignore
    [subscribes, subscribes,];
    var __VLS_47;
    // @ts-ignore
    [];
    var __VLS_41;
}
// @ts-ignore
[];
var __VLS_9;
var __VLS_50;
/** @ts-ignore @type {typeof __VLS_components.nSpin | typeof __VLS_components.NSpin | typeof __VLS_components.nSpin | typeof __VLS_components.NSpin} */
nSpin;
// @ts-ignore
var __VLS_51 = __VLS_asFunctionalComponent1(__VLS_50, new __VLS_50({
    show: (__VLS_ctx.loading),
}));
var __VLS_52 = __VLS_51.apply(void 0, __spreadArray([{
        show: (__VLS_ctx.loading),
    }], __VLS_functionalComponentArgsRest(__VLS_51), false));
var __VLS_55 = __VLS_53.slots.default;
if (!__VLS_ctx.loading && __VLS_ctx.subscribes.length === 0) {
    var __VLS_56 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
    nEmpty;
    // @ts-ignore
    var __VLS_57 = __VLS_asFunctionalComponent1(__VLS_56, new __VLS_56({
        description: (__VLS_ctx.emptyDescription),
    }));
    var __VLS_58 = __VLS_57.apply(void 0, __spreadArray([{
            description: (__VLS_ctx.emptyDescription),
        }], __VLS_functionalComponentArgsRest(__VLS_57), false));
}
else {
    var __VLS_61 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nList | typeof __VLS_components.NList | typeof __VLS_components.nList | typeof __VLS_components.NList} */
    nList;
    // @ts-ignore
    var __VLS_62 = __VLS_asFunctionalComponent1(__VLS_61, new __VLS_61({}));
    var __VLS_63 = __VLS_62.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_62), false));
    var __VLS_66 = __VLS_64.slots.default;
    var _loop_1 = function (subscribe) {
        var __VLS_67 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nListItem | typeof __VLS_components.NListItem | typeof __VLS_components.nListItem | typeof __VLS_components.NListItem} */
        nListItem;
        // @ts-ignore
        var __VLS_68 = __VLS_asFunctionalComponent1(__VLS_67, new __VLS_67({
            key: (subscribe.id),
        }));
        var __VLS_69 = __VLS_68.apply(void 0, __spreadArray([{
                key: (subscribe.id),
            }], __VLS_functionalComponentArgsRest(__VLS_68), false));
        var __VLS_72 = __VLS_70.slots.default;
        {
            var __VLS_73 = __VLS_70.slots.prefix;
            var __VLS_74 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
            nIcon;
            // @ts-ignore
            var __VLS_75 = __VLS_asFunctionalComponent1(__VLS_74, new __VLS_74({
                size: "24",
                color: (__VLS_ctx.getIconColor()),
            }));
            var __VLS_76 = __VLS_75.apply(void 0, __spreadArray([{
                    size: "24",
                    color: (__VLS_ctx.getIconColor()),
                }], __VLS_functionalComponentArgsRest(__VLS_75), false));
            var __VLS_79 = __VLS_77.slots.default;
            var __VLS_80 = (__VLS_ctx.getIcon());
            // @ts-ignore
            var __VLS_81 = __VLS_asFunctionalComponent1(__VLS_80, new __VLS_80({}));
            var __VLS_82 = __VLS_81.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_81), false));
            // @ts-ignore
            [subscribes, subscribes, loading, loading, emptyDescription, getIconColor, getIcon,];
            // @ts-ignore
            [];
        }
        var __VLS_85 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nListItemHeader | typeof __VLS_components.NListItemHeader | typeof __VLS_components.nListItemHeader | typeof __VLS_components.NListItemHeader} */
        nListItemHeader;
        // @ts-ignore
        var __VLS_86 = __VLS_asFunctionalComponent1(__VLS_85, new __VLS_85({}));
        var __VLS_87 = __VLS_86.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_86), false));
        var __VLS_90 = __VLS_88.slots.default;
        var __VLS_91 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
        nSpace;
        // @ts-ignore
        var __VLS_92 = __VLS_asFunctionalComponent1(__VLS_91, new __VLS_91({
            align: "center",
        }));
        var __VLS_93 = __VLS_92.apply(void 0, __spreadArray([{
                align: "center",
            }], __VLS_functionalComponentArgsRest(__VLS_92), false));
        var __VLS_96 = __VLS_94.slots.default;
        var __VLS_97 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nText | typeof __VLS_components.NText | typeof __VLS_components.nText | typeof __VLS_components.NText} */
        nText;
        // @ts-ignore
        var __VLS_98 = __VLS_asFunctionalComponent1(__VLS_97, new __VLS_97({
            strong: true,
        }));
        var __VLS_99 = __VLS_98.apply(void 0, __spreadArray([{
                strong: true,
            }], __VLS_functionalComponentArgsRest(__VLS_98), false));
        var __VLS_102 = __VLS_100.slots.default;
        (subscribe.name);
        // @ts-ignore
        [];
        if (!subscribe.state || subscribe.state === 'active') {
            var __VLS_103 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
            nTag;
            // @ts-ignore
            var __VLS_104 = __VLS_asFunctionalComponent1(__VLS_103, new __VLS_103({
                type: "success",
                size: "small",
            }));
            var __VLS_105 = __VLS_104.apply(void 0, __spreadArray([{
                    type: "success",
                    size: "small",
                }], __VLS_functionalComponentArgsRest(__VLS_104), false));
            var __VLS_108 = __VLS_106.slots.default;
            // @ts-ignore
            [];
        }
        else {
            var __VLS_109 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
            nTag;
            // @ts-ignore
            var __VLS_110 = __VLS_asFunctionalComponent1(__VLS_109, new __VLS_109({
                type: "default",
                size: "small",
            }));
            var __VLS_111 = __VLS_110.apply(void 0, __spreadArray([{
                    type: "default",
                    size: "small",
                }], __VLS_functionalComponentArgsRest(__VLS_110), false));
            var __VLS_114 = __VLS_112.slots.default;
            // @ts-ignore
            [];
        }
        if (subscribe.auto_download) {
            var __VLS_115 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
            nTag;
            // @ts-ignore
            var __VLS_116 = __VLS_asFunctionalComponent1(__VLS_115, new __VLS_115({
                type: "info",
                size: "small",
            }));
            var __VLS_117 = __VLS_116.apply(void 0, __spreadArray([{
                    type: "info",
                    size: "small",
                }], __VLS_functionalComponentArgsRest(__VLS_116), false));
            var __VLS_120 = __VLS_118.slots.default;
            // @ts-ignore
            [];
        }
        // @ts-ignore
        [];
        // @ts-ignore
        [];
        if (subscribe.description) {
            var __VLS_121 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nListItemMeta | typeof __VLS_components.NListItemMeta | typeof __VLS_components.nListItemMeta | typeof __VLS_components.NListItemMeta} */
            nListItemMeta;
            // @ts-ignore
            var __VLS_122 = __VLS_asFunctionalComponent1(__VLS_121, new __VLS_121({}));
            var __VLS_123 = __VLS_122.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_122), false));
            var __VLS_126 = __VLS_124.slots.default;
            (subscribe.description);
            // @ts-ignore
            [];
        }
        {
            var __VLS_127 = __VLS_70.slots.suffix;
            var __VLS_128 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
            nSpace;
            // @ts-ignore
            var __VLS_129 = __VLS_asFunctionalComponent1(__VLS_128, new __VLS_128({}));
            var __VLS_130 = __VLS_129.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_129), false));
            var __VLS_133 = __VLS_131.slots.default;
            var __VLS_134 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
            nButton;
            // @ts-ignore
            var __VLS_135 = __VLS_asFunctionalComponent1(__VLS_134, new __VLS_134(__assign({ 'onClick': {} }, { text: true, size: "small", type: (subscribe.state === 'paused' ? 'success' : 'default') })));
            var __VLS_136 = __VLS_135.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { text: true, size: "small", type: (subscribe.state === 'paused' ? 'success' : 'default') })], __VLS_functionalComponentArgsRest(__VLS_135), false));
            var __VLS_139 = void 0;
            var __VLS_140 = ({ click: {} },
                { onClick: function () {
                        var _a = [];
                        for (var _i = 0; _i < arguments.length; _i++) {
                            _a[_i] = arguments[_i];
                        }
                        var $event = _a[0];
                        if (!!(!__VLS_ctx.loading && __VLS_ctx.subscribes.length === 0))
                            return;
                        __VLS_ctx.toggleState(subscribe);
                        // @ts-ignore
                        [toggleState,];
                    } });
            var __VLS_141 = __VLS_137.slots.default;
            (subscribe.state === 'paused' ? '启用' : '暂停');
            // @ts-ignore
            [];
            var __VLS_142 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
            nButton;
            // @ts-ignore
            var __VLS_143 = __VLS_asFunctionalComponent1(__VLS_142, new __VLS_142(__assign({ 'onClick': {} }, { text: true, size: "small" })));
            var __VLS_144 = __VLS_143.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { text: true, size: "small" })], __VLS_functionalComponentArgsRest(__VLS_143), false));
            var __VLS_147 = void 0;
            var __VLS_148 = ({ click: {} },
                { onClick: function () {
                        var _a = [];
                        for (var _i = 0; _i < arguments.length; _i++) {
                            _a[_i] = arguments[_i];
                        }
                        var $event = _a[0];
                        if (!!(!__VLS_ctx.loading && __VLS_ctx.subscribes.length === 0))
                            return;
                        __VLS_ctx.$emit('edit', subscribe);
                        // @ts-ignore
                        [$emit,];
                    } });
            var __VLS_149 = __VLS_145.slots.default;
            // @ts-ignore
            [];
            var __VLS_150 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
            nButton;
            // @ts-ignore
            var __VLS_151 = __VLS_asFunctionalComponent1(__VLS_150, new __VLS_150(__assign({ 'onClick': {} }, { text: true, size: "small", type: "error" })));
            var __VLS_152 = __VLS_151.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { text: true, size: "small", type: "error" })], __VLS_functionalComponentArgsRest(__VLS_151), false));
            var __VLS_155 = void 0;
            var __VLS_156 = ({ click: {} },
                { onClick: function () {
                        var _a = [];
                        for (var _i = 0; _i < arguments.length; _i++) {
                            _a[_i] = arguments[_i];
                        }
                        var $event = _a[0];
                        if (!!(!__VLS_ctx.loading && __VLS_ctx.subscribes.length === 0))
                            return;
                        __VLS_ctx.$emit('delete', subscribe);
                        // @ts-ignore
                        [$emit,];
                    } });
            var __VLS_157 = __VLS_153.slots.default;
            // @ts-ignore
            [];
            // @ts-ignore
            [];
            // @ts-ignore
            [];
        }
        // @ts-ignore
        [];
        // @ts-ignore
        [];
    };
    var __VLS_77, __VLS_100, __VLS_106, __VLS_112, __VLS_118, __VLS_94, __VLS_88, __VLS_124, __VLS_137, __VLS_138, __VLS_145, __VLS_146, __VLS_153, __VLS_154, __VLS_131, __VLS_70;
    for (var _i = 0, _a = __VLS_vFor((__VLS_ctx.subscribes)); _i < _a.length; _i++) {
        var subscribe = _a[_i][0];
        _loop_1(subscribe);
    }
    // @ts-ignore
    [];
    var __VLS_64;
}
// @ts-ignore
[];
var __VLS_53;
// @ts-ignore
[];
var __VLS_3;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({
    __typeEmits: {},
    __typeProps: {},
});
exports.default = {};
