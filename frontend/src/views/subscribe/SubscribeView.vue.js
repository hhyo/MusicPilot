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
var SubscribeList_vue_1 = require("./SubscribeList.vue");
var SubscribeHistory_vue_1 = require("./SubscribeHistory.vue");
var subscribeApi = require("@/api/subscribe");
var message = (0, naive_ui_1.useMessage)();
var dialog = (0, naive_ui_1.useDialog)();
var activeTab = (0, vue_1.ref)('artist');
var showCreateModal = (0, vue_1.ref)(false);
var submitting = (0, vue_1.ref)(false);
var editingSubscribe = (0, vue_1.ref)(null);
var formRef = (0, vue_1.ref)(null);
var form = (0, vue_1.ref)({
    type: 'artist',
    source_type: 'netease',
    id: '',
    name: '',
    description: '',
    auto_download: true,
    download_format: 'FLAC',
    rules_json: ''
});
var typeOptions = [
    { label: '艺术家', value: 'artist' },
    { label: '专辑', value: 'album' },
    { label: '歌单', value: 'playlist' },
    { label: '榜单', value: 'chart' }
];
var sourceTypeOptions = [
    { label: '网易云音乐', value: 'netease' },
    { label: 'QQ音乐', value: 'qq' }
];
var formatOptions = [
    { label: 'FLAC', value: 'FLAC' },
    { label: 'MP3', value: 'MP3' },
    { label: 'APE', value: 'APE' }
];
var rules = {
    type: { required: true, message: '请选择订阅类型' },
    id: { required: true, message: '请输入 ID' },
    name: { required: true, message: '请输入名称' }
};
var subscribes = (0, vue_1.ref)([]);
var allSubscribes = (0, vue_1.computed)(function () { return subscribes.value; });
var artistSubscribes = (0, vue_1.computed)(function () { return subscribes.value.filter(function (s) { return s.type === 'artist'; }); });
var albumSubscribes = (0, vue_1.computed)(function () { return subscribes.value.filter(function (s) { return s.type === 'album'; }); });
var playlistSubscribes = (0, vue_1.computed)(function () { return subscribes.value.filter(function (s) { return s.type === 'playlist'; }); });
var chartSubscribes = (0, vue_1.computed)(function () { return subscribes.value.filter(function (s) { return s.type === 'chart'; }); });
var idLabel = (0, vue_1.computed)(function () {
    switch (form.value.type) {
        case 'artist':
        case 'album':
            return 'MusicBrainz ID';
        case 'playlist':
            return '歌单 ID';
        case 'chart':
            return '榜单 ID';
        default:
            return 'ID';
    }
});
var idPlaceholder = (0, vue_1.computed)(function () {
    switch (form.value.type) {
        case 'artist':
            return '例如：d36e608f-5491-4b9f-9657-90e7c7b5b2ad';
        case 'album':
            return '例如：8a2d8f3a-4b3e-4c2d-9a1f-2b3c4d5e6f7g';
        case 'playlist':
            return '例如：3778678';
        case 'chart':
            return '例如：19723756（飙升榜）';
        default:
            return '请输入 ID';
    }
});
var loadSubscribes = function () { return __awaiter(void 0, void 0, void 0, function () {
    var data, error_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                return [4 /*yield*/, subscribeApi.listSubscribes()];
            case 1:
                data = _a.sent();
                subscribes.value = data.items || [];
                return [3 /*break*/, 3];
            case 2:
                error_1 = _a.sent();
                message.error('加载订阅失败');
                return [3 /*break*/, 3];
            case 3: return [2 /*return*/];
        }
    });
}); };
var handleTabChange = function () {
    // 切换标签时刷新
};
var handleEdit = function (subscribe) {
    editingSubscribe.value = subscribe;
    form.value = {
        type: subscribe.type,
        source_type: subscribe.source_type,
        id: subscribe.musicbrainz_id || subscribe.playlist_id || '',
        name: subscribe.name,
        description: subscribe.description || '',
        auto_download: subscribe.auto_download,
        download_format: subscribe.download_format,
        rules_json: subscribe.rules ? JSON.stringify(subscribe.rules, null, 2) : ''
    };
    showCreateModal.value = true;
};
var handleDelete = function (subscribe) {
    dialog.warning({
        title: '确认删除',
        content: "\u786E\u5B9A\u8981\u5220\u9664\u8BA2\u9605 \"".concat(subscribe.name, "\" \u5417\uFF1F"),
        positiveText: '删除',
        negativeText: '取消',
        onPositiveClick: function () { return __awaiter(void 0, void 0, void 0, function () {
            var error_2;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        _a.trys.push([0, 3, , 4]);
                        return [4 /*yield*/, subscribeApi.deleteSubscribe(subscribe.id)];
                    case 1:
                        _a.sent();
                        message.success('删除成功');
                        return [4 /*yield*/, loadSubscribes()];
                    case 2:
                        _a.sent();
                        return [3 /*break*/, 4];
                    case 3:
                        error_2 = _a.sent();
                        message.error('删除失败');
                        return [3 /*break*/, 4];
                    case 4: return [2 /*return*/];
                }
            });
        }); }
    });
};
var handleSubmit = function () { return __awaiter(void 0, void 0, void 0, function () {
    var payload, error_3;
    var _a;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 7, 8, 9]);
                return [4 /*yield*/, ((_a = formRef.value) === null || _a === void 0 ? void 0 : _a.validate())];
            case 1:
                _b.sent();
                submitting.value = true;
                payload = {
                    type: form.value.type,
                    source_type: form.value.source_type,
                    name: form.value.name,
                    description: form.value.description,
                    auto_download: form.value.auto_download,
                    download_format: form.value.download_format
                };
                // 设置 ID 字段
                if (form.value.type === 'artist' || form.value.type === 'album') {
                    payload.musicbrainz_id = form.value.id;
                }
                else {
                    payload.playlist_id = form.value.id;
                }
                // 解析规则
                if (form.value.rules_json) {
                    try {
                        payload.rules = JSON.parse(form.value.rules_json);
                    }
                    catch (_c) {
                        message.error('订阅规则格式错误');
                        return [2 /*return*/];
                    }
                }
                if (!editingSubscribe.value) return [3 /*break*/, 3];
                return [4 /*yield*/, subscribeApi.updateSubscribe(editingSubscribe.value.id, payload)];
            case 2:
                _b.sent();
                message.success('更新成功');
                return [3 /*break*/, 5];
            case 3: return [4 /*yield*/, subscribeApi.createSubscribe(payload)];
            case 4:
                _b.sent();
                message.success('创建成功');
                _b.label = 5;
            case 5:
                showCreateModal.value = false;
                editingSubscribe.value = null;
                return [4 /*yield*/, loadSubscribes()];
            case 6:
                _b.sent();
                return [3 /*break*/, 9];
            case 7:
                error_3 = _b.sent();
                if (error_3 === null || error_3 === void 0 ? void 0 : error_3.errorFields) {
                    // 表单验证错误
                    return [2 /*return*/];
                }
                message.error(editingSubscribe.value ? '更新失败' : '创建失败');
                return [3 /*break*/, 9];
            case 8:
                submitting.value = false;
                return [7 /*endfinally*/];
            case 9: return [2 /*return*/];
        }
    });
}); };
var resetForm = function () {
    form.value = {
        type: 'artist',
        source_type: 'netease',
        id: '',
        name: '',
        description: '',
        auto_download: true,
        download_format: 'FLAC',
        rules_json: ''
    };
};
// 监听模态框关闭，重置表单
watch(showCreateModal, function (val) {
    if (!val) {
        resetForm();
        editingSubscribe.value = null;
    }
});
(0, vue_1.onMounted)(function () {
    loadSubscribes();
});
var __VLS_ctx = __assign(__assign({}, {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "subscribe-view" }));
/** @type {__VLS_StyleScopedClasses['subscribe-view']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader | typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader} */
nPageHeader;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    title: "订阅管理",
}));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([{
        title: "订阅管理",
    }], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5 = __VLS_3.slots.default;
{
    var __VLS_6 = __VLS_3.slots.extra;
    var __VLS_7 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_8 = __VLS_asFunctionalComponent1(__VLS_7, new __VLS_7(__assign({ 'onClick': {} }, { type: "primary" })));
    var __VLS_9 = __VLS_8.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary" })], __VLS_functionalComponentArgsRest(__VLS_8), false));
    var __VLS_12 = void 0;
    var __VLS_13 = ({ click: {} },
        { onClick: function () {
                var _a = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    _a[_i] = arguments[_i];
                }
                var $event = _a[0];
                __VLS_ctx.showCreateModal = true;
                // @ts-ignore
                [showCreateModal,];
            } });
    var __VLS_14 = __VLS_10.slots.default;
    {
        var __VLS_15 = __VLS_10.slots.icon;
        var __VLS_16 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
        nIcon;
        // @ts-ignore
        var __VLS_17 = __VLS_asFunctionalComponent1(__VLS_16, new __VLS_16({}));
        var __VLS_18 = __VLS_17.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_17), false));
        var __VLS_21 = __VLS_19.slots.default;
        var __VLS_22 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.AddIcon} */
        ionicons5_1.AddOutline;
        // @ts-ignore
        var __VLS_23 = __VLS_asFunctionalComponent1(__VLS_22, new __VLS_22({}));
        var __VLS_24 = __VLS_23.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_23), false));
        // @ts-ignore
        [];
        var __VLS_19;
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_10;
    var __VLS_11;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_3;
var __VLS_27;
/** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
nCard;
// @ts-ignore
var __VLS_28 = __VLS_asFunctionalComponent1(__VLS_27, new __VLS_27({}));
var __VLS_29 = __VLS_28.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_28), false));
var __VLS_32 = __VLS_30.slots.default;
var __VLS_33;
/** @ts-ignore @type {typeof __VLS_components.nTabs | typeof __VLS_components.NTabs | typeof __VLS_components.nTabs | typeof __VLS_components.NTabs} */
nTabs;
// @ts-ignore
var __VLS_34 = __VLS_asFunctionalComponent1(__VLS_33, new __VLS_33(__assign({ 'onUpdate:value': {} }, { value: (__VLS_ctx.activeTab), type: "line" })));
var __VLS_35 = __VLS_34.apply(void 0, __spreadArray([__assign({ 'onUpdate:value': {} }, { value: (__VLS_ctx.activeTab), type: "line" })], __VLS_functionalComponentArgsRest(__VLS_34), false));
var __VLS_38;
var __VLS_39 = ({ 'update:value': {} },
    { 'onUpdate:value': (__VLS_ctx.handleTabChange) });
var __VLS_40 = __VLS_36.slots.default;
var __VLS_41;
/** @ts-ignore @type {typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane | typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane} */
nTabPane;
// @ts-ignore
var __VLS_42 = __VLS_asFunctionalComponent1(__VLS_41, new __VLS_41({
    name: "artist",
    tab: "艺术家",
}));
var __VLS_43 = __VLS_42.apply(void 0, __spreadArray([{
        name: "artist",
        tab: "艺术家",
    }], __VLS_functionalComponentArgsRest(__VLS_42), false));
var __VLS_46 = __VLS_44.slots.default;
var __VLS_47 = SubscribeList_vue_1.default;
// @ts-ignore
var __VLS_48 = __VLS_asFunctionalComponent1(__VLS_47, new __VLS_47(__assign(__assign(__assign({ 'onRefresh': {} }, { 'onEdit': {} }), { 'onDelete': {} }), { type: "artist", subscribes: (__VLS_ctx.artistSubscribes) })));
var __VLS_49 = __VLS_48.apply(void 0, __spreadArray([__assign(__assign(__assign({ 'onRefresh': {} }, { 'onEdit': {} }), { 'onDelete': {} }), { type: "artist", subscribes: (__VLS_ctx.artistSubscribes) })], __VLS_functionalComponentArgsRest(__VLS_48), false));
var __VLS_52;
var __VLS_53 = ({ refresh: {} },
    { onRefresh: (__VLS_ctx.loadSubscribes) });
var __VLS_54 = ({ edit: {} },
    { onEdit: (__VLS_ctx.handleEdit) });
var __VLS_55 = ({ delete: {} },
    { onDelete: (__VLS_ctx.handleDelete) });
var __VLS_50;
var __VLS_51;
// @ts-ignore
[activeTab, handleTabChange, artistSubscribes, loadSubscribes, handleEdit, handleDelete,];
var __VLS_44;
var __VLS_56;
/** @ts-ignore @type {typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane | typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane} */
nTabPane;
// @ts-ignore
var __VLS_57 = __VLS_asFunctionalComponent1(__VLS_56, new __VLS_56({
    name: "album",
    tab: "专辑",
}));
var __VLS_58 = __VLS_57.apply(void 0, __spreadArray([{
        name: "album",
        tab: "专辑",
    }], __VLS_functionalComponentArgsRest(__VLS_57), false));
var __VLS_61 = __VLS_59.slots.default;
var __VLS_62 = SubscribeList_vue_1.default;
// @ts-ignore
var __VLS_63 = __VLS_asFunctionalComponent1(__VLS_62, new __VLS_62(__assign(__assign(__assign({ 'onRefresh': {} }, { 'onEdit': {} }), { 'onDelete': {} }), { type: "album", subscribes: (__VLS_ctx.albumSubscribes) })));
var __VLS_64 = __VLS_63.apply(void 0, __spreadArray([__assign(__assign(__assign({ 'onRefresh': {} }, { 'onEdit': {} }), { 'onDelete': {} }), { type: "album", subscribes: (__VLS_ctx.albumSubscribes) })], __VLS_functionalComponentArgsRest(__VLS_63), false));
var __VLS_67;
var __VLS_68 = ({ refresh: {} },
    { onRefresh: (__VLS_ctx.loadSubscribes) });
var __VLS_69 = ({ edit: {} },
    { onEdit: (__VLS_ctx.handleEdit) });
var __VLS_70 = ({ delete: {} },
    { onDelete: (__VLS_ctx.handleDelete) });
var __VLS_65;
var __VLS_66;
// @ts-ignore
[loadSubscribes, handleEdit, handleDelete, albumSubscribes,];
var __VLS_59;
var __VLS_71;
/** @ts-ignore @type {typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane | typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane} */
nTabPane;
// @ts-ignore
var __VLS_72 = __VLS_asFunctionalComponent1(__VLS_71, new __VLS_71({
    name: "playlist",
    tab: "歌单",
}));
var __VLS_73 = __VLS_72.apply(void 0, __spreadArray([{
        name: "playlist",
        tab: "歌单",
    }], __VLS_functionalComponentArgsRest(__VLS_72), false));
var __VLS_76 = __VLS_74.slots.default;
var __VLS_77 = SubscribeList_vue_1.default;
// @ts-ignore
var __VLS_78 = __VLS_asFunctionalComponent1(__VLS_77, new __VLS_77(__assign(__assign(__assign({ 'onRefresh': {} }, { 'onEdit': {} }), { 'onDelete': {} }), { type: "playlist", subscribes: (__VLS_ctx.playlistSubscribes) })));
var __VLS_79 = __VLS_78.apply(void 0, __spreadArray([__assign(__assign(__assign({ 'onRefresh': {} }, { 'onEdit': {} }), { 'onDelete': {} }), { type: "playlist", subscribes: (__VLS_ctx.playlistSubscribes) })], __VLS_functionalComponentArgsRest(__VLS_78), false));
var __VLS_82;
var __VLS_83 = ({ refresh: {} },
    { onRefresh: (__VLS_ctx.loadSubscribes) });
var __VLS_84 = ({ edit: {} },
    { onEdit: (__VLS_ctx.handleEdit) });
var __VLS_85 = ({ delete: {} },
    { onDelete: (__VLS_ctx.handleDelete) });
var __VLS_80;
var __VLS_81;
// @ts-ignore
[loadSubscribes, handleEdit, handleDelete, playlistSubscribes,];
var __VLS_74;
var __VLS_86;
/** @ts-ignore @type {typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane | typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane} */
nTabPane;
// @ts-ignore
var __VLS_87 = __VLS_asFunctionalComponent1(__VLS_86, new __VLS_86({
    name: "chart",
    tab: "榜单",
}));
var __VLS_88 = __VLS_87.apply(void 0, __spreadArray([{
        name: "chart",
        tab: "榜单",
    }], __VLS_functionalComponentArgsRest(__VLS_87), false));
var __VLS_91 = __VLS_89.slots.default;
var __VLS_92 = SubscribeList_vue_1.default;
// @ts-ignore
var __VLS_93 = __VLS_asFunctionalComponent1(__VLS_92, new __VLS_92(__assign(__assign(__assign({ 'onRefresh': {} }, { 'onEdit': {} }), { 'onDelete': {} }), { type: "chart", subscribes: (__VLS_ctx.chartSubscribes) })));
var __VLS_94 = __VLS_93.apply(void 0, __spreadArray([__assign(__assign(__assign({ 'onRefresh': {} }, { 'onEdit': {} }), { 'onDelete': {} }), { type: "chart", subscribes: (__VLS_ctx.chartSubscribes) })], __VLS_functionalComponentArgsRest(__VLS_93), false));
var __VLS_97;
var __VLS_98 = ({ refresh: {} },
    { onRefresh: (__VLS_ctx.loadSubscribes) });
var __VLS_99 = ({ edit: {} },
    { onEdit: (__VLS_ctx.handleEdit) });
var __VLS_100 = ({ delete: {} },
    { onDelete: (__VLS_ctx.handleDelete) });
var __VLS_95;
var __VLS_96;
// @ts-ignore
[loadSubscribes, handleEdit, handleDelete, chartSubscribes,];
var __VLS_89;
var __VLS_101;
/** @ts-ignore @type {typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane | typeof __VLS_components.nTabPane | typeof __VLS_components.NTabPane} */
nTabPane;
// @ts-ignore
var __VLS_102 = __VLS_asFunctionalComponent1(__VLS_101, new __VLS_101({
    name: "history",
    tab: "发布记录",
}));
var __VLS_103 = __VLS_102.apply(void 0, __spreadArray([{
        name: "history",
        tab: "发布记录",
    }], __VLS_functionalComponentArgsRest(__VLS_102), false));
var __VLS_106 = __VLS_104.slots.default;
var __VLS_107 = SubscribeHistory_vue_1.default;
// @ts-ignore
var __VLS_108 = __VLS_asFunctionalComponent1(__VLS_107, new __VLS_107({
    subscribes: (__VLS_ctx.allSubscribes),
}));
var __VLS_109 = __VLS_108.apply(void 0, __spreadArray([{
        subscribes: (__VLS_ctx.allSubscribes),
    }], __VLS_functionalComponentArgsRest(__VLS_108), false));
// @ts-ignore
[allSubscribes,];
var __VLS_104;
// @ts-ignore
[];
var __VLS_36;
var __VLS_37;
// @ts-ignore
[];
var __VLS_30;
var __VLS_112;
/** @ts-ignore @type {typeof __VLS_components.nModal | typeof __VLS_components.NModal | typeof __VLS_components.nModal | typeof __VLS_components.NModal} */
nModal;
// @ts-ignore
var __VLS_113 = __VLS_asFunctionalComponent1(__VLS_112, new __VLS_112({
    show: (__VLS_ctx.showCreateModal),
    maskClosable: (false),
}));
var __VLS_114 = __VLS_113.apply(void 0, __spreadArray([{
        show: (__VLS_ctx.showCreateModal),
        maskClosable: (false),
    }], __VLS_functionalComponentArgsRest(__VLS_113), false));
var __VLS_117 = __VLS_115.slots.default;
var __VLS_118;
/** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
nCard;
// @ts-ignore
var __VLS_119 = __VLS_asFunctionalComponent1(__VLS_118, new __VLS_118(__assign({ style: {} }, { title: (__VLS_ctx.editingSubscribe ? '编辑订阅' : '添加订阅'), bordered: (false), size: "huge", role: "dialog", 'aria-modal': "true" })));
var __VLS_120 = __VLS_119.apply(void 0, __spreadArray([__assign({ style: {} }, { title: (__VLS_ctx.editingSubscribe ? '编辑订阅' : '添加订阅'), bordered: (false), size: "huge", role: "dialog", 'aria-modal': "true" })], __VLS_functionalComponentArgsRest(__VLS_119), false));
var __VLS_123 = __VLS_121.slots.default;
var __VLS_124;
/** @ts-ignore @type {typeof __VLS_components.nForm | typeof __VLS_components.NForm | typeof __VLS_components.nForm | typeof __VLS_components.NForm} */
nForm;
// @ts-ignore
var __VLS_125 = __VLS_asFunctionalComponent1(__VLS_124, new __VLS_124({
    model: (__VLS_ctx.form),
    rules: (__VLS_ctx.rules),
    ref: "formRef",
}));
var __VLS_126 = __VLS_125.apply(void 0, __spreadArray([{
        model: (__VLS_ctx.form),
        rules: (__VLS_ctx.rules),
        ref: "formRef",
    }], __VLS_functionalComponentArgsRest(__VLS_125), false));
var __VLS_129 = {};
var __VLS_131 = __VLS_127.slots.default;
var __VLS_132;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_133 = __VLS_asFunctionalComponent1(__VLS_132, new __VLS_132({
    label: "订阅类型",
    path: "type",
}));
var __VLS_134 = __VLS_133.apply(void 0, __spreadArray([{
        label: "订阅类型",
        path: "type",
    }], __VLS_functionalComponentArgsRest(__VLS_133), false));
var __VLS_137 = __VLS_135.slots.default;
var __VLS_138;
/** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
nSelect;
// @ts-ignore
var __VLS_139 = __VLS_asFunctionalComponent1(__VLS_138, new __VLS_138({
    value: (__VLS_ctx.form.type),
    options: (__VLS_ctx.typeOptions),
}));
var __VLS_140 = __VLS_139.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.form.type),
        options: (__VLS_ctx.typeOptions),
    }], __VLS_functionalComponentArgsRest(__VLS_139), false));
// @ts-ignore
[showCreateModal, editingSubscribe, form, form, rules, typeOptions,];
var __VLS_135;
if (__VLS_ctx.form.type !== 'artist' && __VLS_ctx.form.type !== 'album') {
    var __VLS_143 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
    nFormItem;
    // @ts-ignore
    var __VLS_144 = __VLS_asFunctionalComponent1(__VLS_143, new __VLS_143({
        label: "来源类型",
        path: "source_type",
    }));
    var __VLS_145 = __VLS_144.apply(void 0, __spreadArray([{
            label: "来源类型",
            path: "source_type",
        }], __VLS_functionalComponentArgsRest(__VLS_144), false));
    var __VLS_148 = __VLS_146.slots.default;
    var __VLS_149 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
    nSelect;
    // @ts-ignore
    var __VLS_150 = __VLS_asFunctionalComponent1(__VLS_149, new __VLS_149({
        value: (__VLS_ctx.form.source_type),
        options: (__VLS_ctx.sourceTypeOptions),
    }));
    var __VLS_151 = __VLS_150.apply(void 0, __spreadArray([{
            value: (__VLS_ctx.form.source_type),
            options: (__VLS_ctx.sourceTypeOptions),
        }], __VLS_functionalComponentArgsRest(__VLS_150), false));
    // @ts-ignore
    [form, form, form, sourceTypeOptions,];
    var __VLS_146;
}
var __VLS_154;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_155 = __VLS_asFunctionalComponent1(__VLS_154, new __VLS_154({
    label: "ID",
    path: "id",
    label: (__VLS_ctx.idLabel),
}));
var __VLS_156 = __VLS_155.apply(void 0, __spreadArray([{
        label: "ID",
        path: "id",
        label: (__VLS_ctx.idLabel),
    }], __VLS_functionalComponentArgsRest(__VLS_155), false));
var __VLS_159 = __VLS_157.slots.default;
var __VLS_160;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_161 = __VLS_asFunctionalComponent1(__VLS_160, new __VLS_160({
    value: (__VLS_ctx.form.id),
    placeholder: (__VLS_ctx.idPlaceholder),
}));
var __VLS_162 = __VLS_161.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.form.id),
        placeholder: (__VLS_ctx.idPlaceholder),
    }], __VLS_functionalComponentArgsRest(__VLS_161), false));
// @ts-ignore
[form, idLabel, idPlaceholder,];
var __VLS_157;
var __VLS_165;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_166 = __VLS_asFunctionalComponent1(__VLS_165, new __VLS_165({
    label: "名称",
    path: "name",
}));
var __VLS_167 = __VLS_166.apply(void 0, __spreadArray([{
        label: "名称",
        path: "name",
    }], __VLS_functionalComponentArgsRest(__VLS_166), false));
var __VLS_170 = __VLS_168.slots.default;
var __VLS_171;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_172 = __VLS_asFunctionalComponent1(__VLS_171, new __VLS_171({
    value: (__VLS_ctx.form.name),
    placeholder: "订阅名称",
}));
var __VLS_173 = __VLS_172.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.form.name),
        placeholder: "订阅名称",
    }], __VLS_functionalComponentArgsRest(__VLS_172), false));
// @ts-ignore
[form,];
var __VLS_168;
var __VLS_176;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_177 = __VLS_asFunctionalComponent1(__VLS_176, new __VLS_176({
    label: "描述",
    path: "description",
}));
var __VLS_178 = __VLS_177.apply(void 0, __spreadArray([{
        label: "描述",
        path: "description",
    }], __VLS_functionalComponentArgsRest(__VLS_177), false));
var __VLS_181 = __VLS_179.slots.default;
var __VLS_182;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_183 = __VLS_asFunctionalComponent1(__VLS_182, new __VLS_182({
    value: (__VLS_ctx.form.description),
    type: "textarea",
    placeholder: "订阅描述（可选）",
    rows: (3),
}));
var __VLS_184 = __VLS_183.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.form.description),
        type: "textarea",
        placeholder: "订阅描述（可选）",
        rows: (3),
    }], __VLS_functionalComponentArgsRest(__VLS_183), false));
// @ts-ignore
[form,];
var __VLS_179;
var __VLS_187;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_188 = __VLS_asFunctionalComponent1(__VLS_187, new __VLS_187({
    label: "自动下载",
    path: "auto_download",
}));
var __VLS_189 = __VLS_188.apply(void 0, __spreadArray([{
        label: "自动下载",
        path: "auto_download",
    }], __VLS_functionalComponentArgsRest(__VLS_188), false));
var __VLS_192 = __VLS_190.slots.default;
var __VLS_193;
/** @ts-ignore @type {typeof __VLS_components.nSwitch | typeof __VLS_components.NSwitch} */
nSwitch;
// @ts-ignore
var __VLS_194 = __VLS_asFunctionalComponent1(__VLS_193, new __VLS_193({
    value: (__VLS_ctx.form.auto_download),
}));
var __VLS_195 = __VLS_194.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.form.auto_download),
    }], __VLS_functionalComponentArgsRest(__VLS_194), false));
// @ts-ignore
[form,];
var __VLS_190;
if (__VLS_ctx.form.auto_download) {
    var __VLS_198 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
    nFormItem;
    // @ts-ignore
    var __VLS_199 = __VLS_asFunctionalComponent1(__VLS_198, new __VLS_198({
        label: "下载格式",
        path: "download_format",
    }));
    var __VLS_200 = __VLS_199.apply(void 0, __spreadArray([{
            label: "下载格式",
            path: "download_format",
        }], __VLS_functionalComponentArgsRest(__VLS_199), false));
    var __VLS_203 = __VLS_201.slots.default;
    var __VLS_204 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
    nSelect;
    // @ts-ignore
    var __VLS_205 = __VLS_asFunctionalComponent1(__VLS_204, new __VLS_204({
        value: (__VLS_ctx.form.download_format),
        options: (__VLS_ctx.formatOptions),
    }));
    var __VLS_206 = __VLS_205.apply(void 0, __spreadArray([{
            value: (__VLS_ctx.form.download_format),
            options: (__VLS_ctx.formatOptions),
        }], __VLS_functionalComponentArgsRest(__VLS_205), false));
    // @ts-ignore
    [form, form, formatOptions,];
    var __VLS_201;
}
if (__VLS_ctx.form.auto_download && (__VLS_ctx.form.type === 'artist' || __VLS_ctx.form.type === 'album')) {
    var __VLS_209 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
    nFormItem;
    // @ts-ignore
    var __VLS_210 = __VLS_asFunctionalComponent1(__VLS_209, new __VLS_209({
        label: "订阅规则",
        path: "rules",
    }));
    var __VLS_211 = __VLS_210.apply(void 0, __spreadArray([{
            label: "订阅规则",
            path: "rules",
        }], __VLS_functionalComponentArgsRest(__VLS_210), false));
    var __VLS_214 = __VLS_212.slots.default;
    var __VLS_215 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
    nInput;
    // @ts-ignore
    var __VLS_216 = __VLS_asFunctionalComponent1(__VLS_215, new __VLS_215({
        value: (__VLS_ctx.form.rules_json),
        type: "textarea",
        placeholder: '{"format": "FLAC", "min_bitrate": 320, "max_size": 500000000}',
        rows: (3),
    }));
    var __VLS_217 = __VLS_216.apply(void 0, __spreadArray([{
            value: (__VLS_ctx.form.rules_json),
            type: "textarea",
            placeholder: '{"format": "FLAC", "min_bitrate": 320, "max_size": 500000000}',
            rows: (3),
        }], __VLS_functionalComponentArgsRest(__VLS_216), false));
    {
        var __VLS_220 = __VLS_212.slots.feedback;
        // @ts-ignore
        [form, form, form, form,];
    }
    // @ts-ignore
    [];
    var __VLS_212;
}
// @ts-ignore
[];
var __VLS_127;
{
    var __VLS_221 = __VLS_121.slots.footer;
    var __VLS_222 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
    nSpace;
    // @ts-ignore
    var __VLS_223 = __VLS_asFunctionalComponent1(__VLS_222, new __VLS_222({
        justify: "end",
    }));
    var __VLS_224 = __VLS_223.apply(void 0, __spreadArray([{
            justify: "end",
        }], __VLS_functionalComponentArgsRest(__VLS_223), false));
    var __VLS_227 = __VLS_225.slots.default;
    var __VLS_228 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_229 = __VLS_asFunctionalComponent1(__VLS_228, new __VLS_228(__assign({ 'onClick': {} })));
    var __VLS_230 = __VLS_229.apply(void 0, __spreadArray([__assign({ 'onClick': {} })], __VLS_functionalComponentArgsRest(__VLS_229), false));
    var __VLS_233 = void 0;
    var __VLS_234 = ({ click: {} },
        { onClick: function () {
                var _a = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    _a[_i] = arguments[_i];
                }
                var $event = _a[0];
                __VLS_ctx.showCreateModal = false;
                // @ts-ignore
                [showCreateModal,];
            } });
    var __VLS_235 = __VLS_231.slots.default;
    // @ts-ignore
    [];
    var __VLS_231;
    var __VLS_232;
    var __VLS_236 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_237 = __VLS_asFunctionalComponent1(__VLS_236, new __VLS_236(__assign({ 'onClick': {} }, { type: "primary", loading: (__VLS_ctx.submitting) })));
    var __VLS_238 = __VLS_237.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary", loading: (__VLS_ctx.submitting) })], __VLS_functionalComponentArgsRest(__VLS_237), false));
    var __VLS_241 = void 0;
    var __VLS_242 = ({ click: {} },
        { onClick: (__VLS_ctx.handleSubmit) });
    var __VLS_243 = __VLS_239.slots.default;
    (__VLS_ctx.editingSubscribe ? '保存' : '创建');
    // @ts-ignore
    [editingSubscribe, submitting, handleSubmit,];
    var __VLS_239;
    var __VLS_240;
    // @ts-ignore
    [];
    var __VLS_225;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_121;
// @ts-ignore
[];
var __VLS_115;
// @ts-ignore
var __VLS_130 = __VLS_129;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({});
exports.default = {};
