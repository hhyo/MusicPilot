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
var settings = (0, vue_1.ref)({
    appName: 'MusicPilot',
    apiUrl: 'http://localhost:8000',
});
var stats = (0, vue_1.ref)({
    artistCount: 0,
    albumCount: 0,
    trackCount: 0,
    playlistCount: 0,
});
var logs = (0, vue_1.ref)([
    '[2026-02-26 12:00:00] 系统启动',
    '[2026-02-26 12:00:01] 数据库连接成功',
]);
// TODO: 实现设置保存、统计加载、日志获取
function saveSettings() {
    console.log('保存设置:', settings.value);
}
var __VLS_ctx = __assign(__assign({}, {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "system-view" }));
/** @type {__VLS_StyleScopedClasses['system-view']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader} */
nPageHeader;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    title: "系统设置",
}));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([{
        title: "系统设置",
    }], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5;
/** @ts-ignore @type {typeof __VLS_components.nTabs | typeof __VLS_components.NTabs | typeof __VLS_components.nTabs | typeof __VLS_components.NTabs} */
nTabs;
// @ts-ignore
var __VLS_6 = __VLS_asFunctionalComponent1(__VLS_5, new __VLS_5({
    type: "line",
}));
var __VLS_7 = __VLS_6.apply(void 0, __spreadArray([{
        type: "line",
    }], __VLS_functionalComponentArgsRest(__VLS_6), false));
var __VLS_10 = __VLS_8.slots.default;
var __VLS_11;
/** @ts-ignore @type {typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane | typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane} */
nTabPane;
// @ts-ignore
var __VLS_12 = __VLS_asFunctionalComponent1(__VLS_11, new __VLS_11({
    name: "general",
    tab: "常规",
}));
var __VLS_13 = __VLS_12.apply(void 0, __spreadArray([{
        name: "general",
        tab: "常规",
    }], __VLS_functionalComponentArgsRest(__VLS_12), false));
var __VLS_16 = __VLS_14.slots.default;
var __VLS_17;
/** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
nCard;
// @ts-ignore
var __VLS_18 = __VLS_asFunctionalComponent1(__VLS_17, new __VLS_17({
    title: "基本信息",
}));
var __VLS_19 = __VLS_18.apply(void 0, __spreadArray([{
        title: "基本信息",
    }], __VLS_functionalComponentArgsRest(__VLS_18), false));
var __VLS_22 = __VLS_20.slots.default;
var __VLS_23;
/** @ts-ignore @type {typeof __VLS_components.nForm | typeof __VLS_components.NForm | typeof __VLS_components.nForm | typeof __VLS_components.NForm} */
nForm;
// @ts-ignore
var __VLS_24 = __VLS_asFunctionalComponent1(__VLS_23, new __VLS_23({
    labelWidth: (120),
}));
var __VLS_25 = __VLS_24.apply(void 0, __spreadArray([{
        labelWidth: (120),
    }], __VLS_functionalComponentArgsRest(__VLS_24), false));
var __VLS_28 = __VLS_26.slots.default;
var __VLS_29;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_30 = __VLS_asFunctionalComponent1(__VLS_29, new __VLS_29({
    label: "应用名称",
}));
var __VLS_31 = __VLS_30.apply(void 0, __spreadArray([{
        label: "应用名称",
    }], __VLS_functionalComponentArgsRest(__VLS_30), false));
var __VLS_34 = __VLS_32.slots.default;
var __VLS_35;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_36 = __VLS_asFunctionalComponent1(__VLS_35, new __VLS_35({
    value: (__VLS_ctx.settings.appName),
}));
var __VLS_37 = __VLS_36.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.settings.appName),
    }], __VLS_functionalComponentArgsRest(__VLS_36), false));
// @ts-ignore
[settings,];
var __VLS_32;
var __VLS_40;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_41 = __VLS_asFunctionalComponent1(__VLS_40, new __VLS_40({
    label: "API 地址",
}));
var __VLS_42 = __VLS_41.apply(void 0, __spreadArray([{
        label: "API 地址",
    }], __VLS_functionalComponentArgsRest(__VLS_41), false));
var __VLS_45 = __VLS_43.slots.default;
var __VLS_46;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_47 = __VLS_asFunctionalComponent1(__VLS_46, new __VLS_46({
    value: (__VLS_ctx.settings.apiUrl),
}));
var __VLS_48 = __VLS_47.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.settings.apiUrl),
    }], __VLS_functionalComponentArgsRest(__VLS_47), false));
// @ts-ignore
[settings,];
var __VLS_43;
// @ts-ignore
[];
var __VLS_26;
{
    var __VLS_51 = __VLS_20.slots.footer;
    var __VLS_52 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_53 = __VLS_asFunctionalComponent1(__VLS_52, new __VLS_52(__assign({ 'onClick': {} }, { type: "primary" })));
    var __VLS_54 = __VLS_53.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary" })], __VLS_functionalComponentArgsRest(__VLS_53), false));
    var __VLS_57 = void 0;
    var __VLS_58 = ({ click: {} },
        { onClick: (__VLS_ctx.saveSettings) });
    var __VLS_59 = __VLS_55.slots.default;
    // @ts-ignore
    [saveSettings,];
    var __VLS_55;
    var __VLS_56;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_20;
// @ts-ignore
[];
var __VLS_14;
var __VLS_60;
/** @ts-ignore @type {typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane | typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane} */
nTabPane;
// @ts-ignore
var __VLS_61 = __VLS_asFunctionalComponent1(__VLS_60, new __VLS_60({
    name: "stats",
    tab: "统计信息",
}));
var __VLS_62 = __VLS_61.apply(void 0, __spreadArray([{
        name: "stats",
        tab: "统计信息",
    }], __VLS_functionalComponentArgsRest(__VLS_61), false));
var __VLS_65 = __VLS_63.slots.default;
var __VLS_66;
/** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
nCard;
// @ts-ignore
var __VLS_67 = __VLS_asFunctionalComponent1(__VLS_66, new __VLS_66({
    title: "系统统计",
}));
var __VLS_68 = __VLS_67.apply(void 0, __spreadArray([{
        title: "系统统计",
    }], __VLS_functionalComponentArgsRest(__VLS_67), false));
var __VLS_71 = __VLS_69.slots.default;
var __VLS_72;
/** @ts-ignore @type {typeof __VLS_components.nStatistic | typeof __VLS_components.NStatistic} */
nStatistic;
// @ts-ignore
var __VLS_73 = __VLS_asFunctionalComponent1(__VLS_72, new __VLS_72({
    label: "艺术家",
    value: (__VLS_ctx.stats.artistCount),
}));
var __VLS_74 = __VLS_73.apply(void 0, __spreadArray([{
        label: "艺术家",
        value: (__VLS_ctx.stats.artistCount),
    }], __VLS_functionalComponentArgsRest(__VLS_73), false));
var __VLS_77;
/** @ts-ignore @type {typeof __VLS_components.nStatistic | typeof __VLS_components.NStatistic} */
nStatistic;
// @ts-ignore
var __VLS_78 = __VLS_asFunctionalComponent1(__VLS_77, new __VLS_77({
    label: "专辑",
    value: (__VLS_ctx.stats.albumCount),
}));
var __VLS_79 = __VLS_78.apply(void 0, __spreadArray([{
        label: "专辑",
        value: (__VLS_ctx.stats.albumCount),
    }], __VLS_functionalComponentArgsRest(__VLS_78), false));
var __VLS_82;
/** @ts-ignore @type {typeof __VLS_components.nStatistic | typeof __VLS_components.NStatistic} */
nStatistic;
// @ts-ignore
var __VLS_83 = __VLS_asFunctionalComponent1(__VLS_82, new __VLS_82({
    label: "曲目",
    value: (__VLS_ctx.stats.trackCount),
}));
var __VLS_84 = __VLS_83.apply(void 0, __spreadArray([{
        label: "曲目",
        value: (__VLS_ctx.stats.trackCount),
    }], __VLS_functionalComponentArgsRest(__VLS_83), false));
var __VLS_87;
/** @ts-ignore @type {typeof __VLS_components.nStatistic | typeof __VLS_components.NStatistic} */
nStatistic;
// @ts-ignore
var __VLS_88 = __VLS_asFunctionalComponent1(__VLS_87, new __VLS_87({
    label: "播放列表",
    value: (__VLS_ctx.stats.playlistCount),
}));
var __VLS_89 = __VLS_88.apply(void 0, __spreadArray([{
        label: "播放列表",
        value: (__VLS_ctx.stats.playlistCount),
    }], __VLS_functionalComponentArgsRest(__VLS_88), false));
// @ts-ignore
[stats, stats, stats, stats,];
var __VLS_69;
// @ts-ignore
[];
var __VLS_63;
var __VLS_92;
/** @ts-ignore @type {typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane | typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane} */
nTabPane;
// @ts-ignore
var __VLS_93 = __VLS_asFunctionalComponent1(__VLS_92, new __VLS_92({
    name: "logs",
    tab: "日志",
}));
var __VLS_94 = __VLS_93.apply(void 0, __spreadArray([{
        name: "logs",
        tab: "日志",
    }], __VLS_functionalComponentArgsRest(__VLS_93), false));
var __VLS_97 = __VLS_95.slots.default;
var __VLS_98;
/** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
nCard;
// @ts-ignore
var __VLS_99 = __VLS_asFunctionalComponent1(__VLS_98, new __VLS_98({
    title: "系统日志",
}));
var __VLS_100 = __VLS_99.apply(void 0, __spreadArray([{
        title: "系统日志",
    }], __VLS_functionalComponentArgsRest(__VLS_99), false));
var __VLS_103 = __VLS_101.slots.default;
var __VLS_104;
/** @ts-ignore @type {typeof __VLS_components.nLog | typeof __VLS_components.NLog} */
nLog;
// @ts-ignore
var __VLS_105 = __VLS_asFunctionalComponent1(__VLS_104, new __VLS_104({
    log: (__VLS_ctx.logs),
    rows: (20),
}));
var __VLS_106 = __VLS_105.apply(void 0, __spreadArray([{
        log: (__VLS_ctx.logs),
        rows: (20),
    }], __VLS_functionalComponentArgsRest(__VLS_105), false));
// @ts-ignore
[logs,];
var __VLS_101;
// @ts-ignore
[];
var __VLS_95;
// @ts-ignore
[];
var __VLS_8;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({});
exports.default = {};
