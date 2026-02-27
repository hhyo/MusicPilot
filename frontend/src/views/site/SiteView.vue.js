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
var vue_router_1 = require("vue-router");
var naive_ui_1 = require("naive-ui");
var antd_1 = require("@vicons/antd");
var site_1 = require("@/store/site");
var router = (0, vue_router_1.useRouter)();
var dialog = (0, naive_ui_1.useDialog)();
var message = (0, naive_ui_1.useMessage)();
var siteStore = (0, site_1.useSiteStore)();
var sites = siteStore.sites, loading = siteStore.loading, total = siteStore.total;
var showCreateModal = (0, vue_1.ref)(false);
var showDeleteModal = (0, vue_1.ref)(false);
var editingSite = (0, vue_1.ref)(null);
var siteToDelete = (0, vue_1.ref)(null);
var testingSiteId = (0, vue_1.ref)(null);
var formRef = (0, vue_1.ref)(null);
var formData = (0, vue_1.ref)({
    name: '',
    url: '',
    domain: '',
    username: '',
    password: '',
    passkey: '',
    cookie: '',
    proxy: '',
    downloader: 'qbittorrent',
    priority: 1,
    enabled: true,
    site_type: 'resource',
    timeout: 30,
    rss_interval: 60,
});
var downloaderOptions = [
    { label: 'qBittorrent', value: 'qbittorrent' },
    { label: 'Transmission', value: 'transmission' },
];
var formRules = {
    name: [
        { required: true, message: '请输入站点名称', trigger: 'blur' }
    ],
    url: [
        { required: true, message: '请输入站点 URL', trigger: 'blur' },
        { type: 'url', message: '请输入有效的 URL', trigger: 'blur' }
    ],
    downloader: [
        { required: true, message: '请选择下载器', trigger: 'change' }
    ],
};
var handleBack = function () {
    router.back();
};
var handleEdit = function (site) {
    editingSite.value = site;
    formData.value = {
        name: site.name,
        url: site.url,
        domain: site.domain,
        username: site.username,
        password: site.password,
        passkey: site.passkey,
        cookie: site.cookie,
        proxy: site.proxy,
        downloader: site.downloader,
        priority: site.priority,
        enabled: site.enabled,
        site_type: site.site_type,
        timeout: site.timeout,
        rss_interval: site.rss_interval,
    };
    showCreateModal.value = true;
};
var handleTest = function (id) { return __awaiter(void 0, void 0, void 0, function () {
    var response;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                testingSiteId.value = id;
                _a.label = 1;
            case 1:
                _a.trys.push([1, , 3, 4]);
                return [4 /*yield*/, siteStore.testSite(id)];
            case 2:
                response = _a.sent();
                dialog.success({
                    title: '测试结果',
                    content: response.message,
                    positiveText: '确定',
                });
                return [3 /*break*/, 4];
            case 3:
                testingSiteId.value = null;
                return [7 /*endfinally*/];
            case 4: return [2 /*return*/];
        }
    });
}); };
var handleToggle = function (site) { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, siteStore.toggleSite(site.id)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}); };
var handleDelete = function (site) {
    siteToDelete.value = site;
    showDeleteModal.value = true;
};
var confirmDelete = function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                if (!siteToDelete.value) return [3 /*break*/, 2];
                return [4 /*yield*/, siteStore.deleteSite(siteToDelete.value.id)];
            case 1:
                _a.sent();
                showDeleteModal.value = false;
                siteToDelete.value = null;
                _a.label = 2;
            case 2: return [2 /*return*/];
        }
    });
}); };
var handleSaveSite = function () { return __awaiter(void 0, void 0, void 0, function () {
    var error_1;
    var _a;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 6, , 7]);
                return [4 /*yield*/, ((_a = formRef.value) === null || _a === void 0 ? void 0 : _a.validate())];
            case 1:
                _b.sent();
                if (!editingSite.value) return [3 /*break*/, 3];
                // 更新站点
                return [4 /*yield*/, siteStore.updateSite(editingSite.value.id, formData.value)];
            case 2:
                // 更新站点
                _b.sent();
                return [3 /*break*/, 5];
            case 3: 
            // 创建站点
            return [4 /*yield*/, siteStore.createSite(formData.value)];
            case 4:
                // 创建站点
                _b.sent();
                _b.label = 5;
            case 5:
                showCreateModal.value = false;
                editingSite.value = null;
                resetForm();
                return [3 /*break*/, 7];
            case 6:
                error_1 = _b.sent();
                return [3 /*break*/, 7];
            case 7: return [2 /*return*/];
        }
    });
}); };
var resetForm = function () {
    formData.value = {
        name: '',
        url: '',
        domain: '',
        username: '',
        password: '',
        passkey: '',
        cookie: '',
        proxy: '',
        downloader: 'qbittorrent',
        priority: 1,
        enabled: true,
        site_type: 'resource',
        timeout: 30,
        rss_interval: 60,
    };
};
(0, vue_1.onMounted)(function () {
    siteStore.fetchSites();
});
var __VLS_ctx = __assign(__assign({}, {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "site-view" }));
/** @type {__VLS_StyleScopedClasses['site-view']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader | typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader} */
nPageHeader;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0(__assign({ 'onBack': {} }, { title: "站点管理" })));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([__assign({ 'onBack': {} }, { title: "站点管理" })], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5;
var __VLS_6 = ({ back: {} },
    { onBack: (__VLS_ctx.handleBack) });
var __VLS_7 = __VLS_3.slots.default;
{
    var __VLS_8 = __VLS_3.slots.extra;
    var __VLS_9 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_10 = __VLS_asFunctionalComponent1(__VLS_9, new __VLS_9(__assign({ 'onClick': {} }, { type: "primary" })));
    var __VLS_11 = __VLS_10.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary" })], __VLS_functionalComponentArgsRest(__VLS_10), false));
    var __VLS_14 = void 0;
    var __VLS_15 = ({ click: {} },
        { onClick: function () {
                var _a = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    _a[_i] = arguments[_i];
                }
                var $event = _a[0];
                __VLS_ctx.showCreateModal = true;
                // @ts-ignore
                [handleBack, showCreateModal,];
            } });
    var __VLS_16 = __VLS_12.slots.default;
    {
        var __VLS_17 = __VLS_12.slots.icon;
        var __VLS_18 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
        nIcon;
        // @ts-ignore
        var __VLS_19 = __VLS_asFunctionalComponent1(__VLS_18, new __VLS_18({}));
        var __VLS_20 = __VLS_19.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_19), false));
        var __VLS_23 = __VLS_21.slots.default;
        var __VLS_24 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.PlusOutlined} */
        antd_1.PlusOutlined;
        // @ts-ignore
        var __VLS_25 = __VLS_asFunctionalComponent1(__VLS_24, new __VLS_24({}));
        var __VLS_26 = __VLS_25.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_25), false));
        // @ts-ignore
        [];
        var __VLS_21;
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_12;
    var __VLS_13;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_3;
var __VLS_4;
var __VLS_29;
/** @ts-ignore @type {typeof __VLS_components.nSpin | typeof __VLS_components.NSpin | typeof __VLS_components.nSpin | typeof __VLS_components.NSpin} */
nSpin;
// @ts-ignore
var __VLS_30 = __VLS_asFunctionalComponent1(__VLS_29, new __VLS_29({
    show: (__VLS_ctx.loading),
}));
var __VLS_31 = __VLS_30.apply(void 0, __spreadArray([{
        show: (__VLS_ctx.loading),
    }], __VLS_functionalComponentArgsRest(__VLS_30), false));
var __VLS_34 = __VLS_32.slots.default;
if (!__VLS_ctx.loading && !__VLS_ctx.sites.length) {
    var __VLS_35 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
    nEmpty;
    // @ts-ignore
    var __VLS_36 = __VLS_asFunctionalComponent1(__VLS_35, new __VLS_35({
        description: "暂无站点",
    }));
    var __VLS_37 = __VLS_36.apply(void 0, __spreadArray([{
            description: "暂无站点",
        }], __VLS_functionalComponentArgsRest(__VLS_36), false));
}
else {
    var __VLS_40 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nList | typeof __VLS_components.NList | typeof __VLS_components.nList | typeof __VLS_components.NList} */
    nList;
    // @ts-ignore
    var __VLS_41 = __VLS_asFunctionalComponent1(__VLS_40, new __VLS_40({}));
    var __VLS_42 = __VLS_41.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_41), false));
    var __VLS_45 = __VLS_43.slots.default;
    var _loop_1 = function (site) {
        var __VLS_46 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nListItem | typeof __VLS_components.NListItem | typeof __VLS_components.nListItem | typeof __VLS_components.NListItem} */
        nListItem;
        // @ts-ignore
        var __VLS_47 = __VLS_asFunctionalComponent1(__VLS_46, new __VLS_46({
            key: (site.id),
        }));
        var __VLS_48 = __VLS_47.apply(void 0, __spreadArray([{
                key: (site.id),
            }], __VLS_functionalComponentArgsRest(__VLS_47), false));
        var __VLS_51 = __VLS_49.slots.default;
        {
            var __VLS_52 = __VLS_49.slots.prefix;
            var __VLS_53 = void 0;
            /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
            nIcon;
            // @ts-ignore
            var __VLS_54 = __VLS_asFunctionalComponent1(__VLS_53, new __VLS_53({
                size: (24),
                color: (site.enabled ? '#18a058' : '#d03050'),
            }));
            var __VLS_55 = __VLS_54.apply(void 0, __spreadArray([{
                    size: (24),
                    color: (site.enabled ? '#18a058' : '#d03050'),
                }], __VLS_functionalComponentArgsRest(__VLS_54), false));
            var __VLS_58 = __VLS_56.slots.default;
            if (site.enabled) {
                var __VLS_59 = void 0;
                /** @ts-ignore @type {typeof __VLS_components.CloudServerOutlined} */
                antd_1.CloudServerOutlined;
                // @ts-ignore
                var __VLS_60 = __VLS_asFunctionalComponent1(__VLS_59, new __VLS_59({}));
                var __VLS_61 = __VLS_60.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_60), false));
            }
            else {
                var __VLS_64 = void 0;
                /** @ts-ignore @type {typeof __VLS_components.StopOutlined} */
                antd_1.StopOutlined;
                // @ts-ignore
                var __VLS_65 = __VLS_asFunctionalComponent1(__VLS_64, new __VLS_64({}));
                var __VLS_66 = __VLS_65.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_65), false));
            }
            // @ts-ignore
            [loading, loading, sites, sites,];
            // @ts-ignore
            [];
        }
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "site-item" }));
        /** @type {__VLS_StyleScopedClasses['site-item']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "site-info" }));
        /** @type {__VLS_StyleScopedClasses['site-info']} */ ;
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "site-name" }));
        /** @type {__VLS_StyleScopedClasses['site-name']} */ ;
        (site.name);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "site-domain" }));
        /** @type {__VLS_StyleScopedClasses['site-domain']} */ ;
        (site.domain || site.url);
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "site-meta" }));
        /** @type {__VLS_StyleScopedClasses['site-meta']} */ ;
        var __VLS_69 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
        nTag;
        // @ts-ignore
        var __VLS_70 = __VLS_asFunctionalComponent1(__VLS_69, new __VLS_69({
            size: "small",
            type: "info",
        }));
        var __VLS_71 = __VLS_70.apply(void 0, __spreadArray([{
                size: "small",
                type: "info",
            }], __VLS_functionalComponentArgsRest(__VLS_70), false));
        var __VLS_74 = __VLS_72.slots.default;
        (site.downloader);
        // @ts-ignore
        [];
        var __VLS_75 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
        nTag;
        // @ts-ignore
        var __VLS_76 = __VLS_asFunctionalComponent1(__VLS_75, new __VLS_75({
            size: "small",
            type: (site.site_type === 'resource' ? 'success' : 'default'),
        }));
        var __VLS_77 = __VLS_76.apply(void 0, __spreadArray([{
                size: "small",
                type: (site.site_type === 'resource' ? 'success' : 'default'),
            }], __VLS_functionalComponentArgsRest(__VLS_76), false));
        var __VLS_80 = __VLS_78.slots.default;
        (site.site_type === 'resource' ? '资源站点' : '其他');
        // @ts-ignore
        [];
        var __VLS_81 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nTag | typeof __VLS_components.NTag | typeof __VLS_components.nTag | typeof __VLS_components.NTag} */
        nTag;
        // @ts-ignore
        var __VLS_82 = __VLS_asFunctionalComponent1(__VLS_81, new __VLS_81({
            size: "small",
        }));
        var __VLS_83 = __VLS_82.apply(void 0, __spreadArray([{
                size: "small",
            }], __VLS_functionalComponentArgsRest(__VLS_82), false));
        var __VLS_86 = __VLS_84.slots.default;
        (site.priority);
        // @ts-ignore
        [];
        __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "site-actions" }));
        /** @type {__VLS_StyleScopedClasses['site-actions']} */ ;
        var __VLS_87 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButtonGroup | typeof __VLS_components.NButtonGroup | typeof __VLS_components.nButtonGroup | typeof __VLS_components.NButtonGroup} */
        nButtonGroup;
        // @ts-ignore
        var __VLS_88 = __VLS_asFunctionalComponent1(__VLS_87, new __VLS_87({}));
        var __VLS_89 = __VLS_88.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_88), false));
        var __VLS_92 = __VLS_90.slots.default;
        var __VLS_93 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
        nButton;
        // @ts-ignore
        var __VLS_94 = __VLS_asFunctionalComponent1(__VLS_93, new __VLS_93(__assign({ 'onClick': {} }, { size: "small" })));
        var __VLS_95 = __VLS_94.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small" })], __VLS_functionalComponentArgsRest(__VLS_94), false));
        var __VLS_98 = void 0;
        var __VLS_99 = ({ click: {} },
            { onClick: function () {
                    var _a = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        _a[_i] = arguments[_i];
                    }
                    var $event = _a[0];
                    if (!!(!__VLS_ctx.loading && !__VLS_ctx.sites.length))
                        return;
                    __VLS_ctx.handleEdit(site);
                    // @ts-ignore
                    [handleEdit,];
                } });
        var __VLS_100 = __VLS_96.slots.default;
        // @ts-ignore
        [];
        var __VLS_101 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
        nButton;
        // @ts-ignore
        var __VLS_102 = __VLS_asFunctionalComponent1(__VLS_101, new __VLS_101(__assign({ 'onClick': {} }, { size: "small", loading: (__VLS_ctx.testingSiteId === site.id) })));
        var __VLS_103 = __VLS_102.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small", loading: (__VLS_ctx.testingSiteId === site.id) })], __VLS_functionalComponentArgsRest(__VLS_102), false));
        var __VLS_106 = void 0;
        var __VLS_107 = ({ click: {} },
            { onClick: function () {
                    var _a = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        _a[_i] = arguments[_i];
                    }
                    var $event = _a[0];
                    if (!!(!__VLS_ctx.loading && !__VLS_ctx.sites.length))
                        return;
                    __VLS_ctx.handleTest(site.id);
                    // @ts-ignore
                    [testingSiteId, handleTest,];
                } });
        var __VLS_108 = __VLS_104.slots.default;
        // @ts-ignore
        [];
        var __VLS_109 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
        nButton;
        // @ts-ignore
        var __VLS_110 = __VLS_asFunctionalComponent1(__VLS_109, new __VLS_109(__assign({ 'onClick': {} }, { size: "small", type: (site.enabled ? 'warning' : 'success') })));
        var __VLS_111 = __VLS_110.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small", type: (site.enabled ? 'warning' : 'success') })], __VLS_functionalComponentArgsRest(__VLS_110), false));
        var __VLS_114 = void 0;
        var __VLS_115 = ({ click: {} },
            { onClick: function () {
                    var _a = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        _a[_i] = arguments[_i];
                    }
                    var $event = _a[0];
                    if (!!(!__VLS_ctx.loading && !__VLS_ctx.sites.length))
                        return;
                    __VLS_ctx.handleToggle(site);
                    // @ts-ignore
                    [handleToggle,];
                } });
        var __VLS_116 = __VLS_112.slots.default;
        (site.enabled ? '禁用' : '启用');
        // @ts-ignore
        [];
        var __VLS_117 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
        nButton;
        // @ts-ignore
        var __VLS_118 = __VLS_asFunctionalComponent1(__VLS_117, new __VLS_117(__assign({ 'onClick': {} }, { size: "small", type: "error" })));
        var __VLS_119 = __VLS_118.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { size: "small", type: "error" })], __VLS_functionalComponentArgsRest(__VLS_118), false));
        var __VLS_122 = void 0;
        var __VLS_123 = ({ click: {} },
            { onClick: function () {
                    var _a = [];
                    for (var _i = 0; _i < arguments.length; _i++) {
                        _a[_i] = arguments[_i];
                    }
                    var $event = _a[0];
                    if (!!(!__VLS_ctx.loading && !__VLS_ctx.sites.length))
                        return;
                    __VLS_ctx.handleDelete(site);
                    // @ts-ignore
                    [handleDelete,];
                } });
        var __VLS_124 = __VLS_120.slots.default;
        // @ts-ignore
        [];
        // @ts-ignore
        [];
        // @ts-ignore
        [];
        // @ts-ignore
        [];
    };
    var __VLS_56, __VLS_72, __VLS_78, __VLS_84, __VLS_96, __VLS_97, __VLS_104, __VLS_105, __VLS_112, __VLS_113, __VLS_120, __VLS_121, __VLS_90, __VLS_49;
    for (var _i = 0, _a = __VLS_vFor((__VLS_ctx.sites)); _i < _a.length; _i++) {
        var site = _a[_i][0];
        _loop_1(site);
    }
    // @ts-ignore
    [];
    var __VLS_43;
}
// @ts-ignore
[];
var __VLS_32;
var __VLS_125;
/** @ts-ignore @type {typeof __VLS_components.nModal | typeof __VLS_components.NModal | typeof __VLS_components.nModal | typeof __VLS_components.NModal} */
nModal;
// @ts-ignore
var __VLS_126 = __VLS_asFunctionalComponent1(__VLS_125, new __VLS_125(__assign({ 'onPositiveClick': {} }, { show: (__VLS_ctx.showCreateModal), preset: "dialog", title: (__VLS_ctx.editingSite ? '编辑站点' : '添加站点'), positiveText: "确定", negativeText: "取消" })));
var __VLS_127 = __VLS_126.apply(void 0, __spreadArray([__assign({ 'onPositiveClick': {} }, { show: (__VLS_ctx.showCreateModal), preset: "dialog", title: (__VLS_ctx.editingSite ? '编辑站点' : '添加站点'), positiveText: "确定", negativeText: "取消" })], __VLS_functionalComponentArgsRest(__VLS_126), false));
var __VLS_130;
var __VLS_131 = ({ positiveClick: {} },
    { onPositiveClick: (__VLS_ctx.handleSaveSite) });
var __VLS_132 = __VLS_128.slots.default;
var __VLS_133;
/** @ts-ignore @type {typeof __VLS_components.nForm | typeof __VLS_components.NForm | typeof __VLS_components.nForm | typeof __VLS_components.NForm} */
nForm;
// @ts-ignore
var __VLS_134 = __VLS_asFunctionalComponent1(__VLS_133, new __VLS_133({
    ref: "formRef",
    model: (__VLS_ctx.formData),
    rules: (__VLS_ctx.formRules),
    labelPlacement: "left",
    labelWidth: "120px",
    requireMarkPlacement: "right-hanging",
}));
var __VLS_135 = __VLS_134.apply(void 0, __spreadArray([{
        ref: "formRef",
        model: (__VLS_ctx.formData),
        rules: (__VLS_ctx.formRules),
        labelPlacement: "left",
        labelWidth: "120px",
        requireMarkPlacement: "right-hanging",
    }], __VLS_functionalComponentArgsRest(__VLS_134), false));
var __VLS_138 = {};
var __VLS_140 = __VLS_136.slots.default;
var __VLS_141;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_142 = __VLS_asFunctionalComponent1(__VLS_141, new __VLS_141({
    label: "站点名称",
    path: "name",
}));
var __VLS_143 = __VLS_142.apply(void 0, __spreadArray([{
        label: "站点名称",
        path: "name",
    }], __VLS_functionalComponentArgsRest(__VLS_142), false));
var __VLS_146 = __VLS_144.slots.default;
var __VLS_147;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_148 = __VLS_asFunctionalComponent1(__VLS_147, new __VLS_147({
    value: (__VLS_ctx.formData.name),
    placeholder: "请输入站点名称",
}));
var __VLS_149 = __VLS_148.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.name),
        placeholder: "请输入站点名称",
    }], __VLS_functionalComponentArgsRest(__VLS_148), false));
// @ts-ignore
[showCreateModal, editingSite, handleSaveSite, formData, formData, formRules,];
var __VLS_144;
var __VLS_152;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_153 = __VLS_asFunctionalComponent1(__VLS_152, new __VLS_152({
    label: "站点 URL",
    path: "url",
}));
var __VLS_154 = __VLS_153.apply(void 0, __spreadArray([{
        label: "站点 URL",
        path: "url",
    }], __VLS_functionalComponentArgsRest(__VLS_153), false));
var __VLS_157 = __VLS_155.slots.default;
var __VLS_158;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_159 = __VLS_asFunctionalComponent1(__VLS_158, new __VLS_158({
    value: (__VLS_ctx.formData.url),
    placeholder: "https://example.com",
}));
var __VLS_160 = __VLS_159.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.url),
        placeholder: "https://example.com",
    }], __VLS_functionalComponentArgsRest(__VLS_159), false));
// @ts-ignore
[formData,];
var __VLS_155;
var __VLS_163;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_164 = __VLS_asFunctionalComponent1(__VLS_163, new __VLS_163({
    label: "域名",
    path: "domain",
}));
var __VLS_165 = __VLS_164.apply(void 0, __spreadArray([{
        label: "域名",
        path: "domain",
    }], __VLS_functionalComponentArgsRest(__VLS_164), false));
var __VLS_168 = __VLS_166.slots.default;
var __VLS_169;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_170 = __VLS_asFunctionalComponent1(__VLS_169, new __VLS_169({
    value: (__VLS_ctx.formData.domain),
    placeholder: "example.com",
}));
var __VLS_171 = __VLS_170.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.domain),
        placeholder: "example.com",
    }], __VLS_functionalComponentArgsRest(__VLS_170), false));
// @ts-ignore
[formData,];
var __VLS_166;
var __VLS_174;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_175 = __VLS_asFunctionalComponent1(__VLS_174, new __VLS_174({
    label: "用户名",
    path: "username",
}));
var __VLS_176 = __VLS_175.apply(void 0, __spreadArray([{
        label: "用户名",
        path: "username",
    }], __VLS_functionalComponentArgsRest(__VLS_175), false));
var __VLS_179 = __VLS_177.slots.default;
var __VLS_180;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_181 = __VLS_asFunctionalComponent1(__VLS_180, new __VLS_180({
    value: (__VLS_ctx.formData.username),
    placeholder: "请输入用户名",
}));
var __VLS_182 = __VLS_181.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.username),
        placeholder: "请输入用户名",
    }], __VLS_functionalComponentArgsRest(__VLS_181), false));
// @ts-ignore
[formData,];
var __VLS_177;
var __VLS_185;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_186 = __VLS_asFunctionalComponent1(__VLS_185, new __VLS_185({
    label: "密码",
    path: "password",
}));
var __VLS_187 = __VLS_186.apply(void 0, __spreadArray([{
        label: "密码",
        path: "password",
    }], __VLS_functionalComponentArgsRest(__VLS_186), false));
var __VLS_190 = __VLS_188.slots.default;
var __VLS_191;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_192 = __VLS_asFunctionalComponent1(__VLS_191, new __VLS_191({
    value: (__VLS_ctx.formData.password),
    type: "password",
    showPasswordOn: "click",
    placeholder: "请输入密码",
}));
var __VLS_193 = __VLS_192.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.password),
        type: "password",
        showPasswordOn: "click",
        placeholder: "请输入密码",
    }], __VLS_functionalComponentArgsRest(__VLS_192), false));
// @ts-ignore
[formData,];
var __VLS_188;
var __VLS_196;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_197 = __VLS_asFunctionalComponent1(__VLS_196, new __VLS_196({
    label: "Passkey",
    path: "passkey",
}));
var __VLS_198 = __VLS_197.apply(void 0, __spreadArray([{
        label: "Passkey",
        path: "passkey",
    }], __VLS_functionalComponentArgsRest(__VLS_197), false));
var __VLS_201 = __VLS_199.slots.default;
var __VLS_202;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_203 = __VLS_asFunctionalComponent1(__VLS_202, new __VLS_202({
    value: (__VLS_ctx.formData.passkey),
    placeholder: "请输入 Passkey",
}));
var __VLS_204 = __VLS_203.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.passkey),
        placeholder: "请输入 Passkey",
    }], __VLS_functionalComponentArgsRest(__VLS_203), false));
// @ts-ignore
[formData,];
var __VLS_199;
var __VLS_207;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_208 = __VLS_asFunctionalComponent1(__VLS_207, new __VLS_207({
    label: "Cookie",
    path: "cookie",
}));
var __VLS_209 = __VLS_208.apply(void 0, __spreadArray([{
        label: "Cookie",
        path: "cookie",
    }], __VLS_functionalComponentArgsRest(__VLS_208), false));
var __VLS_212 = __VLS_210.slots.default;
var __VLS_213;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_214 = __VLS_asFunctionalComponent1(__VLS_213, new __VLS_213({
    value: (__VLS_ctx.formData.cookie),
    type: "textarea",
    placeholder: "请输入 Cookie",
    rows: (3),
}));
var __VLS_215 = __VLS_214.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.cookie),
        type: "textarea",
        placeholder: "请输入 Cookie",
        rows: (3),
    }], __VLS_functionalComponentArgsRest(__VLS_214), false));
// @ts-ignore
[formData,];
var __VLS_210;
var __VLS_218;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_219 = __VLS_asFunctionalComponent1(__VLS_218, new __VLS_218({
    label: "代理",
    path: "proxy",
}));
var __VLS_220 = __VLS_219.apply(void 0, __spreadArray([{
        label: "代理",
        path: "proxy",
    }], __VLS_functionalComponentArgsRest(__VLS_219), false));
var __VLS_223 = __VLS_221.slots.default;
var __VLS_224;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_225 = __VLS_asFunctionalComponent1(__VLS_224, new __VLS_224({
    value: (__VLS_ctx.formData.proxy),
    placeholder: "http://proxy:port",
}));
var __VLS_226 = __VLS_225.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.proxy),
        placeholder: "http://proxy:port",
    }], __VLS_functionalComponentArgsRest(__VLS_225), false));
// @ts-ignore
[formData,];
var __VLS_221;
var __VLS_229;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_230 = __VLS_asFunctionalComponent1(__VLS_229, new __VLS_229({
    label: "下载器",
    path: "downloader",
}));
var __VLS_231 = __VLS_230.apply(void 0, __spreadArray([{
        label: "下载器",
        path: "downloader",
    }], __VLS_functionalComponentArgsRest(__VLS_230), false));
var __VLS_234 = __VLS_232.slots.default;
var __VLS_235;
/** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
nSelect;
// @ts-ignore
var __VLS_236 = __VLS_asFunctionalComponent1(__VLS_235, new __VLS_235({
    value: (__VLS_ctx.formData.downloader),
    options: (__VLS_ctx.downloaderOptions),
    placeholder: "选择下载器",
}));
var __VLS_237 = __VLS_236.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.downloader),
        options: (__VLS_ctx.downloaderOptions),
        placeholder: "选择下载器",
    }], __VLS_functionalComponentArgsRest(__VLS_236), false));
// @ts-ignore
[formData, downloaderOptions,];
var __VLS_232;
var __VLS_240;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_241 = __VLS_asFunctionalComponent1(__VLS_240, new __VLS_240({
    label: "优先级",
    path: "priority",
}));
var __VLS_242 = __VLS_241.apply(void 0, __spreadArray([{
        label: "优先级",
        path: "priority",
    }], __VLS_functionalComponentArgsRest(__VLS_241), false));
var __VLS_245 = __VLS_243.slots.default;
var __VLS_246;
/** @ts-ignore @type {typeof __VLS_components.nInputNumber | typeof __VLS_components.NInputNumber} */
nInputNumber;
// @ts-ignore
var __VLS_247 = __VLS_asFunctionalComponent1(__VLS_246, new __VLS_246({
    value: (__VLS_ctx.formData.priority),
    min: (1),
    max: (10),
}));
var __VLS_248 = __VLS_247.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.priority),
        min: (1),
        max: (10),
    }], __VLS_functionalComponentArgsRest(__VLS_247), false));
// @ts-ignore
[formData,];
var __VLS_243;
var __VLS_251;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_252 = __VLS_asFunctionalComponent1(__VLS_251, new __VLS_251({
    label: "启用站点",
    path: "enabled",
}));
var __VLS_253 = __VLS_252.apply(void 0, __spreadArray([{
        label: "启用站点",
        path: "enabled",
    }], __VLS_functionalComponentArgsRest(__VLS_252), false));
var __VLS_256 = __VLS_254.slots.default;
var __VLS_257;
/** @ts-ignore @type {typeof __VLS_components.nSwitch | typeof __VLS_components.NSwitch} */
nSwitch;
// @ts-ignore
var __VLS_258 = __VLS_asFunctionalComponent1(__VLS_257, new __VLS_257({
    value: (__VLS_ctx.formData.enabled),
}));
var __VLS_259 = __VLS_258.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.formData.enabled),
    }], __VLS_functionalComponentArgsRest(__VLS_258), false));
// @ts-ignore
[formData,];
var __VLS_254;
// @ts-ignore
[];
var __VLS_136;
// @ts-ignore
[];
var __VLS_128;
var __VLS_129;
var __VLS_262;
/** @ts-ignore @type {typeof __VLS_components.nModal | typeof __VLS_components.NModal} */
nModal;
// @ts-ignore
var __VLS_263 = __VLS_asFunctionalComponent1(__VLS_262, new __VLS_262(__assign({ 'onPositiveClick': {} }, { show: (__VLS_ctx.showDeleteModal), preset: "dialog", title: "确认删除", content: "确定要删除该站点吗？", positiveText: "删除", negativeText: "取消" })));
var __VLS_264 = __VLS_263.apply(void 0, __spreadArray([__assign({ 'onPositiveClick': {} }, { show: (__VLS_ctx.showDeleteModal), preset: "dialog", title: "确认删除", content: "确定要删除该站点吗？", positiveText: "删除", negativeText: "取消" })], __VLS_functionalComponentArgsRest(__VLS_263), false));
var __VLS_267;
var __VLS_268 = ({ positiveClick: {} },
    { onPositiveClick: (__VLS_ctx.confirmDelete) });
var __VLS_265;
var __VLS_266;
// @ts-ignore
var __VLS_139 = __VLS_138;
// @ts-ignore
[showDeleteModal, confirmDelete,];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({});
exports.default = {};
