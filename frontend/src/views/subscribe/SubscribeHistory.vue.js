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
var subscribeApi = require("@/api/subscribe");
var props = defineProps();
var message = (0, naive_ui_1.useMessage)();
var loading = (0, vue_1.ref)(false);
var selectedSubscribeId = (0, vue_1.ref)(null);
var releases = (0, vue_1.ref)([]);
var subscribeOptions = (0, vue_1.computed)(function () {
    return props.subscribes.map(function (s) { return ({
        label: s.name,
        value: s.id
    }); });
});
var columns = [
    {
        title: '订阅',
        key: 'subscribe_name',
        width: 150,
        ellipsis: {
            tooltip: true
        }
    },
    {
        title: '标题',
        key: 'title',
        width: 200,
        ellipsis: {
            tooltip: true
        }
    },
    {
        title: '艺术家',
        key: 'artist',
        width: 150,
        ellipsis: {
            tooltip: true
        }
    },
    {
        title: '类型',
        key: 'release_type',
        width: 80,
        render: function (row) {
            var typeMap = {
                'album': { text: '专辑', type: 'info' },
                'track': { text: '单曲', type: 'default' }
            };
            var type = typeMap[row.release_type] || { text: row.release_type, type: 'default' };
            return (0, vue_1.h)(naive_ui_1.NTag, { type: type.type, size: 'small' }, { default: function () { return type.text; } });
        }
    },
    {
        title: '下载状态',
        key: 'download_status',
        width: 100,
        render: function (row) {
            var statusMap = {
                'pending': { text: '等待中', type: 'default' },
                'downloading': { text: '下载中', type: 'info' },
                'completed': { text: '已完成', type: 'success' },
                'failed': { text: '失败', type: 'error' }
            };
            var status = statusMap[row.download_status] || { text: row.download_status, type: 'default' };
            return (0, vue_1.h)(naive_ui_1.NTag, { type: status.type, size: 'small' }, { default: function () { return status.text; } });
        }
    },
    {
        title: '发布时间',
        key: 'created_at',
        width: 180,
        render: function (row) { return new Date(row.created_at).toLocaleString(); }
    },
    {
        title: '操作',
        key: 'actions',
        width: 100,
        render: function (row) {
            return (0, vue_1.h)(naive_ui_1.NSpace, {}, {
                default: function () { return [
                    (0, vue_1.h)(naive_ui_1.NButton, {
                        text: true,
                        size: 'small',
                        onClick: function () { return viewDetails(row); }
                    }, { default: function () { return '详情'; } })
                ]; }
            });
        }
    }
];
var pagination = {
    pageSize: 20
};
var loadReleases = function () { return __awaiter(void 0, void 0, void 0, function () {
    var data, error_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                loading.value = true;
                _a.label = 1;
            case 1:
                _a.trys.push([1, 6, 7, 8]);
                data = void 0;
                if (!selectedSubscribeId.value) return [3 /*break*/, 3];
                return [4 /*yield*/, subscribeApi.getSubscribeReleases(selectedSubscribeId.value)];
            case 2:
                data = _a.sent();
                return [3 /*break*/, 5];
            case 3: return [4 /*yield*/, subscribeApi.getAllReleases()];
            case 4:
                // 获取所有发布记录
                data = _a.sent();
                _a.label = 5;
            case 5:
                releases.value = data.items || [];
                return [3 /*break*/, 8];
            case 6:
                error_1 = _a.sent();
                message.error('加载发布记录失败');
                return [3 /*break*/, 8];
            case 7:
                loading.value = false;
                return [7 /*endfinally*/];
            case 8: return [2 /*return*/];
        }
    });
}); };
var viewDetails = function (release) {
    // 显示详情对话框
    message.info("\u8BE6\u60C5\uFF1A".concat(release.title));
};
// 监听订阅选择变化
watch(selectedSubscribeId, function () {
    loadReleases();
});
// 初始加载
onMounted(function () {
    loadReleases();
});
var __VLS_ctx = __assign(__assign(__assign(__assign({}, {}), {}), {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "subscribe-history" }));
/** @type {__VLS_StyleScopedClasses['subscribe-history']} */ ;
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
/** @ts-ignore @type {typeof __VLS_components.nText | typeof __VLS_components.NText | typeof __VLS_components.nText | typeof __VLS_components.NText} */
nText;
// @ts-ignore
var __VLS_19 = __VLS_asFunctionalComponent1(__VLS_18, new __VLS_18({
    strong: true,
}));
var __VLS_20 = __VLS_19.apply(void 0, __spreadArray([{
        strong: true,
    }], __VLS_functionalComponentArgsRest(__VLS_19), false));
var __VLS_23 = __VLS_21.slots.default;
var __VLS_21;
var __VLS_15;
var __VLS_24;
/** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
nSpace;
// @ts-ignore
var __VLS_25 = __VLS_asFunctionalComponent1(__VLS_24, new __VLS_24({}));
var __VLS_26 = __VLS_25.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_25), false));
var __VLS_29 = __VLS_27.slots.default;
var __VLS_30;
/** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
nSelect;
// @ts-ignore
var __VLS_31 = __VLS_asFunctionalComponent1(__VLS_30, new __VLS_30(__assign(__assign({ value: (__VLS_ctx.selectedSubscribeId), options: (__VLS_ctx.subscribeOptions), placeholder: "选择订阅" }, { style: {} }), { clearable: true })));
var __VLS_32 = __VLS_31.apply(void 0, __spreadArray([__assign(__assign({ value: (__VLS_ctx.selectedSubscribeId), options: (__VLS_ctx.subscribeOptions), placeholder: "选择订阅" }, { style: {} }), { clearable: true })], __VLS_functionalComponentArgsRest(__VLS_31), false));
// @ts-ignore
[selectedSubscribeId, subscribeOptions,];
var __VLS_27;
// @ts-ignore
[];
var __VLS_9;
var __VLS_35;
/** @ts-ignore @type {typeof __VLS_components.nSpin | typeof __VLS_components.NSpin | typeof __VLS_components.nSpin | typeof __VLS_components.NSpin} */
nSpin;
// @ts-ignore
var __VLS_36 = __VLS_asFunctionalComponent1(__VLS_35, new __VLS_35({
    show: (__VLS_ctx.loading),
}));
var __VLS_37 = __VLS_36.apply(void 0, __spreadArray([{
        show: (__VLS_ctx.loading),
    }], __VLS_functionalComponentArgsRest(__VLS_36), false));
var __VLS_40 = __VLS_38.slots.default;
if (!__VLS_ctx.loading && __VLS_ctx.releases.length === 0) {
    var __VLS_41 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
    nEmpty;
    // @ts-ignore
    var __VLS_42 = __VLS_asFunctionalComponent1(__VLS_41, new __VLS_41({
        description: "暂无发布记录",
    }));
    var __VLS_43 = __VLS_42.apply(void 0, __spreadArray([{
            description: "暂无发布记录",
        }], __VLS_functionalComponentArgsRest(__VLS_42), false));
}
else {
    var __VLS_46 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDataTable | typeof __VLS_components.NDataTable} */
    nDataTable;
    // @ts-ignore
    var __VLS_47 = __VLS_asFunctionalComponent1(__VLS_46, new __VLS_46({
        columns: (__VLS_ctx.columns),
        data: (__VLS_ctx.releases),
        pagination: (__VLS_ctx.pagination),
        bordered: (false),
    }));
    var __VLS_48 = __VLS_47.apply(void 0, __spreadArray([{
            columns: (__VLS_ctx.columns),
            data: (__VLS_ctx.releases),
            pagination: (__VLS_ctx.pagination),
            bordered: (false),
        }], __VLS_functionalComponentArgsRest(__VLS_47), false));
}
// @ts-ignore
[loading, loading, releases, releases, columns, pagination,];
var __VLS_38;
// @ts-ignore
[];
var __VLS_3;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({
    __typeProps: {},
});
exports.default = {};
