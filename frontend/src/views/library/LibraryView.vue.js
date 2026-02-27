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
var library_1 = require("@/store/library");
var libraryStore = (0, library_1.useLibraryStore)();
var loading = (0, vue_1.ref)(false);
var libraries = (0, vue_1.ref)([]);
(0, vue_1.onMounted)(function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        loading.value = true;
        // TODO: 调用 API 获取音乐库列表
        loading.value = false;
        return [2 /*return*/];
    });
}); });
var __VLS_ctx = __assign(__assign({}, {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "library-view" }));
/** @type {__VLS_StyleScopedClasses['library-view']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader} */
nPageHeader;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    title: "音乐库",
}));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([{
        title: "音乐库",
    }], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5;
/** @ts-ignore @type {typeof __VLS_components.nSpin | typeof __VLS_components.NSpin | typeof __VLS_components.nSpin | typeof __VLS_components.NSpin} */
nSpin;
// @ts-ignore
var __VLS_6 = __VLS_asFunctionalComponent1(__VLS_5, new __VLS_5({
    show: (__VLS_ctx.loading),
}));
var __VLS_7 = __VLS_6.apply(void 0, __spreadArray([{
        show: (__VLS_ctx.loading),
    }], __VLS_functionalComponentArgsRest(__VLS_6), false));
var __VLS_10 = __VLS_8.slots.default;
if (!__VLS_ctx.loading && !__VLS_ctx.libraries.length) {
    var __VLS_11 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
    nEmpty;
    // @ts-ignore
    var __VLS_12 = __VLS_asFunctionalComponent1(__VLS_11, new __VLS_11({
        description: "暂无音乐库",
    }));
    var __VLS_13 = __VLS_12.apply(void 0, __spreadArray([{
            description: "暂无音乐库",
        }], __VLS_functionalComponentArgsRest(__VLS_12), false));
}
else {
    var __VLS_16 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nList | typeof __VLS_components.NList | typeof __VLS_components.nList | typeof __VLS_components.NList} */
    nList;
    // @ts-ignore
    var __VLS_17 = __VLS_asFunctionalComponent1(__VLS_16, new __VLS_16({}));
    var __VLS_18 = __VLS_17.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_17), false));
    var __VLS_21 = __VLS_19.slots.default;
    for (var _i = 0, _a = __VLS_vFor((__VLS_ctx.libraries)); _i < _a.length; _i++) {
        var library = _a[_i][0];
        var __VLS_22 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nListItem | typeof __VLS_components.NListItem | typeof __VLS_components.nListItem | typeof __VLS_components.NListItem} */
        nListItem;
        // @ts-ignore
        var __VLS_23 = __VLS_asFunctionalComponent1(__VLS_22, new __VLS_22({
            key: (library.id),
        }));
        var __VLS_24 = __VLS_23.apply(void 0, __spreadArray([{
                key: (library.id),
            }], __VLS_functionalComponentArgsRest(__VLS_23), false));
        var __VLS_27 = __VLS_25.slots.default;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "library-item" }));
        /** @type {__VLS_StyleScopedClasses['library-item']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "library-info" }));
        /** @type {__VLS_StyleScopedClasses['library-info']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "library-name" }));
        /** @type {__VLS_StyleScopedClasses['library-name']} */ ;
        (library.name);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "library-path" }));
        /** @type {__VLS_StyleScopedClasses['library-path']} */ ;
        (library.path);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "library-stats" }));
        /** @type {__VLS_StyleScopedClasses['library-stats']} */ ;
        var __VLS_28 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
        nTag;
        // @ts-ignore
        var __VLS_29 = __VLS_asFunctionalComponent1(__VLS_28, new __VLS_28({}));
        var __VLS_30 = __VLS_29.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_29), false));
        var __VLS_33 = __VLS_31.slots.default;
        (library.trackCount || 0);
        // @ts-ignore
        [loading, loading, libraries, libraries,];
        var __VLS_31;
        var __VLS_34 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
        nTag;
        // @ts-ignore
        var __VLS_35 = __VLS_asFunctionalComponent1(__VLS_34, new __VLS_34({}));
        var __VLS_36 = __VLS_35.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_35), false));
        var __VLS_39 = __VLS_37.slots.default;
        (library.albumCount || 0);
        // @ts-ignore
        [];
        var __VLS_37;
        // @ts-ignore
        [];
        var __VLS_25;
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_19;
}
// @ts-ignore
[];
var __VLS_8;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({});
exports.default = {};
