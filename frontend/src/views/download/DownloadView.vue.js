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
var RefreshIcon = ionicons5_1.Refresh;
var DownloadIcon = ionicons5_1.DownloadOutline;
var PlayIcon = ionicons5_1.PlayCircleOutline;
var RetryIcon = ionicons5_1.RefreshOutline;
var message = (0, naive_ui_1.useMessage)();
var dialog = (0, naive_ui_1.useDialog)();
// 状态
var loading = (0, vue_1.ref)(false);
var searching = (0, vue_1.ref)(false);
var downloadingByUrl = (0, vue_1.ref)(false);
var showSearchModal = (0, vue_1.ref)(false);
var showUrlModal = (0, vue_1.ref)(false);
var activeTab = (0, vue_1.ref)('downloading');
// 下载任务
var activeDownloads = (0, vue_1.ref)([]);
var completedDownloads = (0, vue_1.ref)([]);
var failedDownloads = (0, vue_1.ref)([]);
var downloadHistory = (0, vue_1.ref)([]);
// 统计
var stats = (0, vue_1.ref)({
    total: 0,
    completed: 0,
    failed: 0,
});
// 计算成功率
var successRate = (0, vue_1.computed)(function () {
    var total = stats.value.completed + stats.value.failed;
    return total > 0 ? Math.round((stats.value.completed / total) * 100) : 0;
});
// 表单引用
var searchFormRef = (0, vue_1.ref)(null);
var urlFormRef = (0, vue_1.ref)(null);
// 搜索表单
var searchForm = (0, vue_1.ref)({
    keyword: '',
    source: 'netease',
    quality: 'standard',
    limit: 1,
});
// URL 表单
var urlForm = (0, vue_1.ref)({
    url: '',
    source: 'netease',
    quality: 'standard',
    title: '',
    artist: '',
    album: '',
});
// 选项
var sourceOptions = [
    { label: '网易云音乐', value: 'netease' },
    // TODO: 添加其他来源
];
var qualityOptions = [
    { label: '标准 (128kbps)', value: 'standard' },
    { label: '高品质 (320kbps)', value: 'high' },
    { label: '无损 (FLAC)', value: 'lossless' },
];
// 表格列定义（使用 h 函数代替 JSX）
var downloadingColumns = [
    {
        title: '标题',
        key: 'title',
        render: function (row) { return row.title || row.task_id; },
    },
    {
        title: '艺术家',
        key: 'artist',
        render: function (row) { return row.artist || '-'; },
    },
    {
        title: '专辑',
        key: 'album',
        render: function (row) { return row.album || '-'; },
    },
    {
        title: '音质',
        key: 'quality',
        render: function (row) {
            var qualityMap = {
                standard: '标准',
                high: '高品质',
                lossless: '无损',
            };
            return qualityMap[row.quality] || row.quality;
        },
    },
    {
        title: '进度',
        key: 'progress',
        render: function (row) {
            var percentage = (row.progress || 0) * 100;
            return (0, vue_1.h)(naive_ui_1.NProgress, { percentage: percentage, indicatorPlacement: 'inside', processing: true });
        },
    },
    {
        title: '状态',
        key: 'status',
        render: function () { return (0, vue_1.h)(naive_ui_1.NTag, { type: 'info' }, function () { return '下载中'; }); },
    },
    {
        title: '操作',
        key: 'actions',
        render: function (row) {
            return (0, vue_1.h)(naive_ui_1.NSpace, null, {
                default: function () { return (0, vue_1.h)(naive_ui_1.NButton, { size: 'small', onClick: function () { return cancelDownload(row.task_id); } }, function () { return '取消'; }); }
            });
        },
    },
];
var completedColumns = [
    {
        title: '标题',
        key: 'title',
        render: function (row) { return row.title || row.task_id; },
    },
    {
        title: '艺术家',
        key: 'artist',
        render: function (row) { return row.artist || '-'; },
    },
    {
        title: '专辑',
        key: 'album',
        render: function (row) { return row.album || '-'; },
    },
    {
        title: '音质',
        key: 'quality',
        render: function (row) {
            var qualityMap = {
                standard: '标准',
                high: '高品质',
                lossless: '无损',
            };
            return qualityMap[row.quality] || row.quality;
        },
    },
    {
        title: '文件大小',
        key: 'file_size',
        render: function (row) { return row.total_bytes ? formatFileSize(row.total_bytes) : '-'; },
    },
    {
        title: '文件路径',
        key: 'file_path',
        render: function (row) { return row.file_path || '-'; },
    },
    {
        title: '操作',
        key: 'actions',
        render: function (row) {
            return (0, vue_1.h)(naive_ui_1.NSpace, null, {
                default: function () { return (0, vue_1.h)(naive_ui_1.NButton, { size: 'small', type: 'primary', onClick: function () { return playTrack(row.file_path); } }, {
                    default: function () { return [(0, vue_1.h)(naive_ui_1.NIcon, null, { default: function () { return (0, vue_1.h)(PlayIcon); } }), '播放']; }
                }); }
            });
        },
    },
];
var failedColumns = [
    {
        title: '标题',
        key: 'title',
        render: function (row) { return row.title || row.task_id; },
    },
    {
        title: '艺术家',
        key: 'artist',
        render: function (row) { return row.artist || '-'; },
    },
    {
        title: '专辑',
        key: 'album',
        render: function (row) { return row.album || '-'; },
    },
    {
        title: '错误信息',
        key: 'error_message',
        render: function (row) { return row.error_message || '-'; },
    },
    {
        title: '操作',
        key: 'actions',
        render: function (row) {
            return (0, vue_1.h)(naive_ui_1.NSpace, null, {
                default: function () { return (0, vue_1.h)(naive_ui_1.NButton, { size: 'small', onClick: function () { return retryDownload(row); } }, {
                    default: function () { return [(0, vue_1.h)(naive_ui_1.NIcon, null, { default: function () { return (0, vue_1.h)(RetryIcon); } }), '重试']; }
                }); }
            });
        },
    },
];
var historyColumns = [
    {
        title: '标题',
        key: 'title',
        render: function (row) { return row.title || '-'; },
    },
    {
        title: '艺术家',
        key: 'artist',
        render: function (row) { return row.artist || '-'; },
    },
    {
        title: '专辑',
        key: 'album',
        render: function (row) { return row.album || '-'; },
    },
    {
        title: '来源',
        key: 'source',
        render: function (row) {
            var sourceMap = {
                netease: '网易云音乐',
            };
            return sourceMap[row.source] || row.source;
        },
    },
    {
        title: '状态',
        key: 'status',
        render: function (row) {
            var statusMap = {
                pending: { type: 'default', text: '等待中' },
                downloading: { type: 'info', text: '下载中' },
                completed: { type: 'success', text: '已完成' },
                failed: { type: 'error', text: '失败' },
                cancelled: { type: 'warning', text: '已取消' },
            };
            var status = statusMap[row.status] || { type: 'default', text: row.status };
            return (0, vue_1.h)(naive_ui_1.NTag, { type: status.type }, function () { return status.text; });
        },
    },
    {
        title: '时间',
        key: 'created_at',
        render: function (row) { return row.created_at ? formatDate(row.created_at) : '-'; },
    },
];
// 方法
var refresh = function () { return __awaiter(void 0, void 0, void 0, function () {
    var error_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                loading.value = true;
                _a.label = 1;
            case 1:
                _a.trys.push([1, 3, 4, 5]);
                return [4 /*yield*/, Promise.all([
                        fetchActiveDownloads(),
                        fetchCompletedDownloads(),
                        fetchFailedDownloads(),
                        fetchDownloadHistory(),
                        fetchStats(),
                    ])];
            case 2:
                _a.sent();
                message.success('刷新成功');
                return [3 /*break*/, 5];
            case 3:
                error_1 = _a.sent();
                message.error('刷新失败');
                return [3 /*break*/, 5];
            case 4:
                loading.value = false;
                return [7 /*endfinally*/];
            case 5: return [2 /*return*/];
        }
    });
}); };
var fetchActiveDownloads = function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        return [2 /*return*/];
    });
}); };
var fetchCompletedDownloads = function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        return [2 /*return*/];
    });
}); };
var fetchFailedDownloads = function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        return [2 /*return*/];
    });
}); };
var fetchDownloadHistory = function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        return [2 /*return*/];
    });
}); };
var fetchStats = function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        return [2 /*return*/];
    });
}); };
var handleSearchAndDownload = function () { return __awaiter(void 0, void 0, void 0, function () {
    var error_2;
    var _a;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 3, 4, 5]);
                return [4 /*yield*/, ((_a = searchFormRef.value) === null || _a === void 0 ? void 0 : _a.validate())];
            case 1:
                _b.sent();
                searching.value = true;
                // TODO: 调用 API 搜索并下载
                // await api.post('/api/v1/downloads/search-and-download', searchForm.value)
                message.success('下载任务已添加');
                showSearchModal.value = false;
                // 刷新下载列表
                return [4 /*yield*/, refresh()
                    // 重置表单
                ];
            case 2:
                // 刷新下载列表
                _b.sent();
                // 重置表单
                searchForm.value = {
                    keyword: '',
                    source: 'netease',
                    quality: 'standard',
                    limit: 1,
                };
                return [3 /*break*/, 5];
            case 3:
                error_2 = _b.sent();
                if (error_2.errors) {
                    // 表单验证错误
                    return [2 /*return*/];
                }
                message.error(error_2.message || '下载失败');
                return [3 /*break*/, 5];
            case 4:
                searching.value = false;
                return [7 /*endfinally*/];
            case 5: return [2 /*return*/];
        }
    });
}); };
var handleUrlDownload = function () { return __awaiter(void 0, void 0, void 0, function () {
    var error_3;
    var _a;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 3, 4, 5]);
                return [4 /*yield*/, ((_a = urlFormRef.value) === null || _a === void 0 ? void 0 : _a.validate())];
            case 1:
                _b.sent();
                downloadingByUrl.value = true;
                // TODO: 调用 API 通过 URL 下载
                // await api.post('/api/v1/downloads/download-by-url', urlForm.value)
                message.success('下载任务已添加');
                showUrlModal.value = false;
                // 刷新下载列表
                return [4 /*yield*/, refresh()
                    // 重置表单
                ];
            case 2:
                // 刷新下载列表
                _b.sent();
                // 重置表单
                urlForm.value = {
                    url: '',
                    source: 'netease',
                    quality: 'standard',
                    title: '',
                    artist: '',
                    album: '',
                };
                return [3 /*break*/, 5];
            case 3:
                error_3 = _b.sent();
                if (error_3.errors) {
                    return [2 /*return*/];
                }
                message.error(error_3.message || '下载失败');
                return [3 /*break*/, 5];
            case 4:
                downloadingByUrl.value = false;
                return [7 /*endfinally*/];
            case 5: return [2 /*return*/];
        }
    });
}); };
var cancelDownload = function (taskId) { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        dialog.warning({
            title: '取消下载',
            content: '确定要取消这个下载任务吗？',
            positiveText: '确定',
            negativeText: '取消',
            onPositiveClick: function () { return __awaiter(void 0, void 0, void 0, function () {
                var error_4;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0:
                            _a.trys.push([0, 2, , 3]);
                            // TODO: 调用 API 取消下载
                            // await api.post(`/api/v1/downloads/${taskId}/cancel`)
                            message.success('已取消下载');
                            return [4 /*yield*/, refresh()];
                        case 1:
                            _a.sent();
                            return [3 /*break*/, 3];
                        case 2:
                            error_4 = _a.sent();
                            message.error('取消失败');
                            return [3 /*break*/, 3];
                        case 3: return [2 /*return*/];
                    }
                });
            }); },
        });
        return [2 /*return*/];
    });
}); };
var retryDownload = function (task) { return __awaiter(void 0, void 0, void 0, function () {
    var error_5;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                // TODO: 调用 API 重试下载
                // await api.post(`/api/v1/downloads/${task.task_id}/retry`)
                message.success('已重新开始下载');
                return [4 /*yield*/, refresh()];
            case 1:
                _a.sent();
                return [3 /*break*/, 3];
            case 2:
                error_5 = _a.sent();
                message.error('重试失败');
                return [3 /*break*/, 3];
            case 3: return [2 /*return*/];
        }
    });
}); };
var playTrack = function (filePath) { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        // TODO: 调用播放器播放
        // playerStore.playTrack(filePath)
        message.info('播放功能待实现');
        return [2 /*return*/];
    });
}); };
var formatFileSize = function (bytes) {
    if (bytes === 0)
        return '0 B';
    var k = 1024;
    var sizes = ['B', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};
var formatDate = function (dateStr) {
    var date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
};
// 定时刷新下载状态
var refreshTimer = null;
(0, vue_1.onMounted)(function () { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, refresh()
                // 每 5 秒刷新一次活跃下载
            ];
            case 1:
                _a.sent();
                // 每 5 秒刷新一次活跃下载
                refreshTimer = setInterval(function () { return __awaiter(void 0, void 0, void 0, function () {
                    return __generator(this, function (_a) {
                        switch (_a.label) {
                            case 0:
                                if (!(activeTab.value === 'downloading')) return [3 /*break*/, 2];
                                return [4 /*yield*/, fetchActiveDownloads()];
                            case 1:
                                _a.sent();
                                _a.label = 2;
                            case 2: return [2 /*return*/];
                        }
                    });
                }); }, 5000);
                return [2 /*return*/];
        }
    });
}); });
(0, vue_1.onUnmounted)(function () {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
});
var __VLS_ctx = __assign(__assign({}, {}), {});
var __VLS_components;
var __VLS_intrinsics;
var __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)(__assign({ class: "download-view" }));
/** @type {__VLS_StyleScopedClasses['download-view']} */ ;
var __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader | typeof __VLS_components.nPageHeader | typeof __VLS_components.NPageHeader} */
nPageHeader;
// @ts-ignore
var __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    title: "下载管理",
}));
var __VLS_2 = __VLS_1.apply(void 0, __spreadArray([{
        title: "下载管理",
    }], __VLS_functionalComponentArgsRest(__VLS_1), false));
var __VLS_5 = __VLS_3.slots.default;
{
    var __VLS_6 = __VLS_3.slots.extra;
    var __VLS_7 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
    nSpace;
    // @ts-ignore
    var __VLS_8 = __VLS_asFunctionalComponent1(__VLS_7, new __VLS_7({}));
    var __VLS_9 = __VLS_8.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_8), false));
    var __VLS_12 = __VLS_10.slots.default;
    var __VLS_13 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_14 = __VLS_asFunctionalComponent1(__VLS_13, new __VLS_13(__assign({ 'onClick': {} }, { loading: (__VLS_ctx.loading) })));
    var __VLS_15 = __VLS_14.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { loading: (__VLS_ctx.loading) })], __VLS_functionalComponentArgsRest(__VLS_14), false));
    var __VLS_18 = void 0;
    var __VLS_19 = ({ click: {} },
        { onClick: (__VLS_ctx.refresh) });
    var __VLS_20 = __VLS_16.slots.default;
    {
        var __VLS_21 = __VLS_16.slots.icon;
        var __VLS_22 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
        nIcon;
        // @ts-ignore
        var __VLS_23 = __VLS_asFunctionalComponent1(__VLS_22, new __VLS_22({}));
        var __VLS_24 = __VLS_23.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_23), false));
        var __VLS_27 = __VLS_25.slots.default;
        var __VLS_28 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.RefreshIcon} */
        RefreshIcon;
        // @ts-ignore
        var __VLS_29 = __VLS_asFunctionalComponent1(__VLS_28, new __VLS_28({}));
        var __VLS_30 = __VLS_29.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_29), false));
        // @ts-ignore
        [loading, refresh,];
        var __VLS_25;
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_16;
    var __VLS_17;
    var __VLS_33 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_34 = __VLS_asFunctionalComponent1(__VLS_33, new __VLS_33(__assign({ 'onClick': {} }, { type: "primary" })));
    var __VLS_35 = __VLS_34.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary" })], __VLS_functionalComponentArgsRest(__VLS_34), false));
    var __VLS_38 = void 0;
    var __VLS_39 = ({ click: {} },
        { onClick: function () {
                var _a = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    _a[_i] = arguments[_i];
                }
                var $event = _a[0];
                __VLS_ctx.showSearchModal = true;
                // @ts-ignore
                [showSearchModal,];
            } });
    var __VLS_40 = __VLS_36.slots.default;
    {
        var __VLS_41 = __VLS_36.slots.icon;
        var __VLS_42 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nIcon | typeof __VLS_components.NIcon | typeof __VLS_components.nIcon | typeof __VLS_components.NIcon} */
        nIcon;
        // @ts-ignore
        var __VLS_43 = __VLS_asFunctionalComponent1(__VLS_42, new __VLS_42({}));
        var __VLS_44 = __VLS_43.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_43), false));
        var __VLS_47 = __VLS_45.slots.default;
        var __VLS_48 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.DownloadIcon} */
        DownloadIcon;
        // @ts-ignore
        var __VLS_49 = __VLS_asFunctionalComponent1(__VLS_48, new __VLS_48({}));
        var __VLS_50 = __VLS_49.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_49), false));
        // @ts-ignore
        [];
        var __VLS_45;
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_36;
    var __VLS_37;
    // @ts-ignore
    [];
    var __VLS_10;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_3;
var __VLS_53;
/** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
nCard;
// @ts-ignore
var __VLS_54 = __VLS_asFunctionalComponent1(__VLS_53, new __VLS_53(__assign({ class: "stats-card" }, { title: "下载统计" })));
var __VLS_55 = __VLS_54.apply(void 0, __spreadArray([__assign({ class: "stats-card" }, { title: "下载统计" })], __VLS_functionalComponentArgsRest(__VLS_54), false));
/** @type {__VLS_StyleScopedClasses['stats-card']} */ ;
var __VLS_58 = __VLS_56.slots.default;
var __VLS_59;
/** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
nSpace;
// @ts-ignore
var __VLS_60 = __VLS_asFunctionalComponent1(__VLS_59, new __VLS_59({
    justify: "space-around",
}));
var __VLS_61 = __VLS_60.apply(void 0, __spreadArray([{
        justify: "space-around",
    }], __VLS_functionalComponentArgsRest(__VLS_60), false));
var __VLS_64 = __VLS_62.slots.default;
var __VLS_65;
/** @ts-ignore @type {typeof __VLS_components.nStatistic | typeof __VLS_components.NStatistic} */
nStatistic;
// @ts-ignore
var __VLS_66 = __VLS_asFunctionalComponent1(__VLS_65, new __VLS_65({
    label: "总下载量",
    value: (__VLS_ctx.stats.total),
}));
var __VLS_67 = __VLS_66.apply(void 0, __spreadArray([{
        label: "总下载量",
        value: (__VLS_ctx.stats.total),
    }], __VLS_functionalComponentArgsRest(__VLS_66), false));
var __VLS_70;
/** @ts-ignore @type {typeof __VLS_components.nStatistic | typeof __VLS_components.NStatistic} */
nStatistic;
// @ts-ignore
var __VLS_71 = __VLS_asFunctionalComponent1(__VLS_70, new __VLS_70({
    label: "成功",
    value: (__VLS_ctx.stats.completed),
}));
var __VLS_72 = __VLS_71.apply(void 0, __spreadArray([{
        label: "成功",
        value: (__VLS_ctx.stats.completed),
    }], __VLS_functionalComponentArgsRest(__VLS_71), false));
var __VLS_75;
/** @ts-ignore @type {typeof __VLS_components.nStatistic | typeof __VLS_components.NStatistic} */
nStatistic;
// @ts-ignore
var __VLS_76 = __VLS_asFunctionalComponent1(__VLS_75, new __VLS_75({
    label: "失败",
    value: (__VLS_ctx.stats.failed),
}));
var __VLS_77 = __VLS_76.apply(void 0, __spreadArray([{
        label: "失败",
        value: (__VLS_ctx.stats.failed),
    }], __VLS_functionalComponentArgsRest(__VLS_76), false));
var __VLS_80;
/** @ts-ignore @type {typeof __VLS_components.nStatistic | typeof __VLS_components.NStatistic} */
nStatistic;
// @ts-ignore
var __VLS_81 = __VLS_asFunctionalComponent1(__VLS_80, new __VLS_80({
    label: "成功率",
    value: (__VLS_ctx.successRate + '%'),
}));
var __VLS_82 = __VLS_81.apply(void 0, __spreadArray([{
        label: "成功率",
        value: (__VLS_ctx.successRate + '%'),
    }], __VLS_functionalComponentArgsRest(__VLS_81), false));
// @ts-ignore
[stats, stats, stats, successRate,];
var __VLS_62;
// @ts-ignore
[];
var __VLS_56;
var __VLS_85;
/** @ts-ignore @type {typeof __VLS_components.nCard | typeof __VLS_components.NCard | typeof __VLS_components.nCard | typeof __VLS_components.NCard} */
nCard;
// @ts-ignore
var __VLS_86 = __VLS_asFunctionalComponent1(__VLS_85, new __VLS_85({}));
var __VLS_87 = __VLS_86.apply(void 0, __spreadArray([{}], __VLS_functionalComponentArgsRest(__VLS_86), false));
var __VLS_90 = __VLS_88.slots.default;
{
    var __VLS_91 = __VLS_88.slots["header-extra"];
    var __VLS_92 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nRadioGroup | typeof __VLS_components.NRadioGroup | typeof __VLS_components.nRadioGroup | typeof __VLS_components.NRadioGroup} */
    nRadioGroup;
    // @ts-ignore
    var __VLS_93 = __VLS_asFunctionalComponent1(__VLS_92, new __VLS_92({
        value: (__VLS_ctx.activeTab),
        size: "small",
    }));
    var __VLS_94 = __VLS_93.apply(void 0, __spreadArray([{
            value: (__VLS_ctx.activeTab),
            size: "small",
        }], __VLS_functionalComponentArgsRest(__VLS_93), false));
    var __VLS_97 = __VLS_95.slots.default;
    var __VLS_98 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nRadioButton | typeof __VLS_components.NRadioButton | typeof __VLS_components.nRadioButton | typeof __VLS_components.NRadioButton} */
    nRadioButton;
    // @ts-ignore
    var __VLS_99 = __VLS_asFunctionalComponent1(__VLS_98, new __VLS_98({
        value: "downloading",
    }));
    var __VLS_100 = __VLS_99.apply(void 0, __spreadArray([{
            value: "downloading",
        }], __VLS_functionalComponentArgsRest(__VLS_99), false));
    var __VLS_103 = __VLS_101.slots.default;
    // @ts-ignore
    [activeTab,];
    var __VLS_101;
    var __VLS_104 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nRadioButton | typeof __VLS_components.NRadioButton | typeof __VLS_components.nRadioButton | typeof __VLS_components.NRadioButton} */
    nRadioButton;
    // @ts-ignore
    var __VLS_105 = __VLS_asFunctionalComponent1(__VLS_104, new __VLS_104({
        value: "completed",
    }));
    var __VLS_106 = __VLS_105.apply(void 0, __spreadArray([{
            value: "completed",
        }], __VLS_functionalComponentArgsRest(__VLS_105), false));
    var __VLS_109 = __VLS_107.slots.default;
    // @ts-ignore
    [];
    var __VLS_107;
    var __VLS_110 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nRadioButton | typeof __VLS_components.NRadioButton | typeof __VLS_components.nRadioButton | typeof __VLS_components.NRadioButton} */
    nRadioButton;
    // @ts-ignore
    var __VLS_111 = __VLS_asFunctionalComponent1(__VLS_110, new __VLS_110({
        value: "failed",
    }));
    var __VLS_112 = __VLS_111.apply(void 0, __spreadArray([{
            value: "failed",
        }], __VLS_functionalComponentArgsRest(__VLS_111), false));
    var __VLS_115 = __VLS_113.slots.default;
    // @ts-ignore
    [];
    var __VLS_113;
    var __VLS_116 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nRadioButton | typeof __VLS_components.NRadioButton | typeof __VLS_components.nRadioButton | typeof __VLS_components.NRadioButton} */
    nRadioButton;
    // @ts-ignore
    var __VLS_117 = __VLS_asFunctionalComponent1(__VLS_116, new __VLS_116({
        value: "history",
    }));
    var __VLS_118 = __VLS_117.apply(void 0, __spreadArray([{
            value: "history",
        }], __VLS_functionalComponentArgsRest(__VLS_117), false));
    var __VLS_121 = __VLS_119.slots.default;
    // @ts-ignore
    [];
    var __VLS_119;
    // @ts-ignore
    [];
    var __VLS_95;
    // @ts-ignore
    [];
}
if (__VLS_ctx.activeTab === 'downloading') {
    var __VLS_122 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDataTable | typeof __VLS_components.NDataTable} */
    nDataTable;
    // @ts-ignore
    var __VLS_123 = __VLS_asFunctionalComponent1(__VLS_122, new __VLS_122({
        columns: (__VLS_ctx.downloadingColumns),
        data: (__VLS_ctx.activeDownloads),
        loading: (__VLS_ctx.loading),
        pagination: ({ pageSize: 10 }),
        rowKey: "task_id",
    }));
    var __VLS_124 = __VLS_123.apply(void 0, __spreadArray([{
            columns: (__VLS_ctx.downloadingColumns),
            data: (__VLS_ctx.activeDownloads),
            loading: (__VLS_ctx.loading),
            pagination: ({ pageSize: 10 }),
            rowKey: "task_id",
        }], __VLS_functionalComponentArgsRest(__VLS_123), false));
    if (!__VLS_ctx.loading && __VLS_ctx.activeDownloads.length === 0) {
        var __VLS_127 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
        nEmpty;
        // @ts-ignore
        var __VLS_128 = __VLS_asFunctionalComponent1(__VLS_127, new __VLS_127({
            description: "没有正在下载的任务",
        }));
        var __VLS_129 = __VLS_128.apply(void 0, __spreadArray([{
                description: "没有正在下载的任务",
            }], __VLS_functionalComponentArgsRest(__VLS_128), false));
    }
}
else if (__VLS_ctx.activeTab === 'completed') {
    var __VLS_132 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDataTable | typeof __VLS_components.NDataTable} */
    nDataTable;
    // @ts-ignore
    var __VLS_133 = __VLS_asFunctionalComponent1(__VLS_132, new __VLS_132({
        columns: (__VLS_ctx.completedColumns),
        data: (__VLS_ctx.completedDownloads),
        loading: (__VLS_ctx.loading),
        pagination: ({ pageSize: 10 }),
        rowKey: "task_id",
    }));
    var __VLS_134 = __VLS_133.apply(void 0, __spreadArray([{
            columns: (__VLS_ctx.completedColumns),
            data: (__VLS_ctx.completedDownloads),
            loading: (__VLS_ctx.loading),
            pagination: ({ pageSize: 10 }),
            rowKey: "task_id",
        }], __VLS_functionalComponentArgsRest(__VLS_133), false));
    if (!__VLS_ctx.loading && __VLS_ctx.completedDownloads.length === 0) {
        var __VLS_137 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
        nEmpty;
        // @ts-ignore
        var __VLS_138 = __VLS_asFunctionalComponent1(__VLS_137, new __VLS_137({
            description: "没有已完成的下载",
        }));
        var __VLS_139 = __VLS_138.apply(void 0, __spreadArray([{
                description: "没有已完成的下载",
            }], __VLS_functionalComponentArgsRest(__VLS_138), false));
    }
}
else if (__VLS_ctx.activeTab === 'failed') {
    var __VLS_142 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDataTable | typeof __VLS_components.NDataTable} */
    nDataTable;
    // @ts-ignore
    var __VLS_143 = __VLS_asFunctionalComponent1(__VLS_142, new __VLS_142({
        columns: (__VLS_ctx.failedColumns),
        data: (__VLS_ctx.failedDownloads),
        loading: (__VLS_ctx.loading),
        pagination: ({ pageSize: 10 }),
        rowKey: "task_id",
    }));
    var __VLS_144 = __VLS_143.apply(void 0, __spreadArray([{
            columns: (__VLS_ctx.failedColumns),
            data: (__VLS_ctx.failedDownloads),
            loading: (__VLS_ctx.loading),
            pagination: ({ pageSize: 10 }),
            rowKey: "task_id",
        }], __VLS_functionalComponentArgsRest(__VLS_143), false));
    if (!__VLS_ctx.loading && __VLS_ctx.failedDownloads.length === 0) {
        var __VLS_147 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
        nEmpty;
        // @ts-ignore
        var __VLS_148 = __VLS_asFunctionalComponent1(__VLS_147, new __VLS_147({
            description: "没有失败的下载",
        }));
        var __VLS_149 = __VLS_148.apply(void 0, __spreadArray([{
                description: "没有失败的下载",
            }], __VLS_functionalComponentArgsRest(__VLS_148), false));
    }
}
else {
    var __VLS_152 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nDataTable | typeof __VLS_components.NDataTable} */
    nDataTable;
    // @ts-ignore
    var __VLS_153 = __VLS_asFunctionalComponent1(__VLS_152, new __VLS_152({
        columns: (__VLS_ctx.historyColumns),
        data: (__VLS_ctx.downloadHistory),
        loading: (__VLS_ctx.loading),
        pagination: ({ pageSize: 20 }),
        rowKey: "source_id",
    }));
    var __VLS_154 = __VLS_153.apply(void 0, __spreadArray([{
            columns: (__VLS_ctx.historyColumns),
            data: (__VLS_ctx.downloadHistory),
            loading: (__VLS_ctx.loading),
            pagination: ({ pageSize: 20 }),
            rowKey: "source_id",
        }], __VLS_functionalComponentArgsRest(__VLS_153), false));
    if (!__VLS_ctx.loading && __VLS_ctx.downloadHistory.length === 0) {
        var __VLS_157 = void 0;
        /** @ts-ignore @type {typeof __VLS_components.nEmpty | typeof __VLS_components.NEmpty} */
        nEmpty;
        // @ts-ignore
        var __VLS_158 = __VLS_asFunctionalComponent1(__VLS_157, new __VLS_157({
            description: "没有下载历史",
        }));
        var __VLS_159 = __VLS_158.apply(void 0, __spreadArray([{
                description: "没有下载历史",
            }], __VLS_functionalComponentArgsRest(__VLS_158), false));
    }
}
// @ts-ignore
[loading, loading, loading, loading, loading, loading, loading, loading, activeTab, activeTab, activeTab, downloadingColumns, activeDownloads, activeDownloads, completedColumns, completedDownloads, completedDownloads, failedColumns, failedDownloads, failedDownloads, historyColumns, downloadHistory, downloadHistory,];
var __VLS_88;
var __VLS_162;
/** @ts-ignore @type {typeof __VLS_components.nModal | typeof __VLS_components.NModal | typeof __VLS_components.nModal | typeof __VLS_components.NModal} */
nModal;
// @ts-ignore
var __VLS_163 = __VLS_asFunctionalComponent1(__VLS_162, new __VLS_162(__assign({ show: (__VLS_ctx.showSearchModal), preset: "card", title: "搜索并下载" }, { style: {} })));
var __VLS_164 = __VLS_163.apply(void 0, __spreadArray([__assign({ show: (__VLS_ctx.showSearchModal), preset: "card", title: "搜索并下载" }, { style: {} })], __VLS_functionalComponentArgsRest(__VLS_163), false));
var __VLS_167 = __VLS_165.slots.default;
var __VLS_168;
/** @ts-ignore @type {typeof __VLS_components.nForm | typeof __VLS_components.NForm | typeof __VLS_components.nForm | typeof __VLS_components.NForm} */
nForm;
// @ts-ignore
var __VLS_169 = __VLS_asFunctionalComponent1(__VLS_168, new __VLS_168({
    ref: "searchFormRef",
    model: (__VLS_ctx.searchForm),
    labelPlacement: "left",
    labelWidth: "80",
}));
var __VLS_170 = __VLS_169.apply(void 0, __spreadArray([{
        ref: "searchFormRef",
        model: (__VLS_ctx.searchForm),
        labelPlacement: "left",
        labelWidth: "80",
    }], __VLS_functionalComponentArgsRest(__VLS_169), false));
var __VLS_173 = {};
var __VLS_175 = __VLS_171.slots.default;
var __VLS_176;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_177 = __VLS_asFunctionalComponent1(__VLS_176, new __VLS_176({
    label: "关键词",
    path: "keyword",
    rule: ({ required: true, message: '请输入关键词' }),
}));
var __VLS_178 = __VLS_177.apply(void 0, __spreadArray([{
        label: "关键词",
        path: "keyword",
        rule: ({ required: true, message: '请输入关键词' }),
    }], __VLS_functionalComponentArgsRest(__VLS_177), false));
var __VLS_181 = __VLS_179.slots.default;
var __VLS_182;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_183 = __VLS_asFunctionalComponent1(__VLS_182, new __VLS_182({
    value: (__VLS_ctx.searchForm.keyword),
    placeholder: "歌曲名、艺术家或专辑",
}));
var __VLS_184 = __VLS_183.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.searchForm.keyword),
        placeholder: "歌曲名、艺术家或专辑",
    }], __VLS_functionalComponentArgsRest(__VLS_183), false));
// @ts-ignore
[showSearchModal, searchForm, searchForm,];
var __VLS_179;
var __VLS_187;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_188 = __VLS_asFunctionalComponent1(__VLS_187, new __VLS_187({
    label: "来源",
    path: "source",
}));
var __VLS_189 = __VLS_188.apply(void 0, __spreadArray([{
        label: "来源",
        path: "source",
    }], __VLS_functionalComponentArgsRest(__VLS_188), false));
var __VLS_192 = __VLS_190.slots.default;
var __VLS_193;
/** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
nSelect;
// @ts-ignore
var __VLS_194 = __VLS_asFunctionalComponent1(__VLS_193, new __VLS_193({
    value: (__VLS_ctx.searchForm.source),
    options: (__VLS_ctx.sourceOptions),
    placeholder: "选择下载来源",
}));
var __VLS_195 = __VLS_194.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.searchForm.source),
        options: (__VLS_ctx.sourceOptions),
        placeholder: "选择下载来源",
    }], __VLS_functionalComponentArgsRest(__VLS_194), false));
// @ts-ignore
[searchForm, sourceOptions,];
var __VLS_190;
var __VLS_198;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_199 = __VLS_asFunctionalComponent1(__VLS_198, new __VLS_198({
    label: "音质",
    path: "quality",
}));
var __VLS_200 = __VLS_199.apply(void 0, __spreadArray([{
        label: "音质",
        path: "quality",
    }], __VLS_functionalComponentArgsRest(__VLS_199), false));
var __VLS_203 = __VLS_201.slots.default;
var __VLS_204;
/** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
nSelect;
// @ts-ignore
var __VLS_205 = __VLS_asFunctionalComponent1(__VLS_204, new __VLS_204({
    value: (__VLS_ctx.searchForm.quality),
    options: (__VLS_ctx.qualityOptions),
    placeholder: "选择音质",
}));
var __VLS_206 = __VLS_205.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.searchForm.quality),
        options: (__VLS_ctx.qualityOptions),
        placeholder: "选择音质",
    }], __VLS_functionalComponentArgsRest(__VLS_205), false));
// @ts-ignore
[searchForm, qualityOptions,];
var __VLS_201;
var __VLS_209;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_210 = __VLS_asFunctionalComponent1(__VLS_209, new __VLS_209({
    label: "数量",
    path: "limit",
}));
var __VLS_211 = __VLS_210.apply(void 0, __spreadArray([{
        label: "数量",
        path: "limit",
    }], __VLS_functionalComponentArgsRest(__VLS_210), false));
var __VLS_214 = __VLS_212.slots.default;
var __VLS_215;
/** @ts-ignore @type {typeof __VLS_components.nInputNumber | typeof __VLS_components.NInputNumber} */
nInputNumber;
// @ts-ignore
var __VLS_216 = __VLS_asFunctionalComponent1(__VLS_215, new __VLS_215({
    value: (__VLS_ctx.searchForm.limit),
    min: (1),
    max: (20),
    placeholder: "下载数量",
}));
var __VLS_217 = __VLS_216.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.searchForm.limit),
        min: (1),
        max: (20),
        placeholder: "下载数量",
    }], __VLS_functionalComponentArgsRest(__VLS_216), false));
// @ts-ignore
[searchForm,];
var __VLS_212;
// @ts-ignore
[];
var __VLS_171;
{
    var __VLS_220 = __VLS_165.slots.footer;
    var __VLS_221 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
    nSpace;
    // @ts-ignore
    var __VLS_222 = __VLS_asFunctionalComponent1(__VLS_221, new __VLS_221({
        justify: "end",
    }));
    var __VLS_223 = __VLS_222.apply(void 0, __spreadArray([{
            justify: "end",
        }], __VLS_functionalComponentArgsRest(__VLS_222), false));
    var __VLS_226 = __VLS_224.slots.default;
    var __VLS_227 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_228 = __VLS_asFunctionalComponent1(__VLS_227, new __VLS_227(__assign({ 'onClick': {} })));
    var __VLS_229 = __VLS_228.apply(void 0, __spreadArray([__assign({ 'onClick': {} })], __VLS_functionalComponentArgsRest(__VLS_228), false));
    var __VLS_232 = void 0;
    var __VLS_233 = ({ click: {} },
        { onClick: function () {
                var _a = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    _a[_i] = arguments[_i];
                }
                var $event = _a[0];
                __VLS_ctx.showSearchModal = false;
                // @ts-ignore
                [showSearchModal,];
            } });
    var __VLS_234 = __VLS_230.slots.default;
    // @ts-ignore
    [];
    var __VLS_230;
    var __VLS_231;
    var __VLS_235 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_236 = __VLS_asFunctionalComponent1(__VLS_235, new __VLS_235(__assign({ 'onClick': {} }, { type: "primary", loading: (__VLS_ctx.searching) })));
    var __VLS_237 = __VLS_236.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary", loading: (__VLS_ctx.searching) })], __VLS_functionalComponentArgsRest(__VLS_236), false));
    var __VLS_240 = void 0;
    var __VLS_241 = ({ click: {} },
        { onClick: (__VLS_ctx.handleSearchAndDownload) });
    var __VLS_242 = __VLS_238.slots.default;
    // @ts-ignore
    [searching, handleSearchAndDownload,];
    var __VLS_238;
    var __VLS_239;
    // @ts-ignore
    [];
    var __VLS_224;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_165;
var __VLS_243;
/** @ts-ignore @type {typeof __VLS_components.nModal | typeof __VLS_components.NModal | typeof __VLS_components.nModal | typeof __VLS_components.NModal} */
nModal;
// @ts-ignore
var __VLS_244 = __VLS_asFunctionalComponent1(__VLS_243, new __VLS_243(__assign({ show: (__VLS_ctx.showUrlModal), preset: "card", title: "通过 URL 下载" }, { style: {} })));
var __VLS_245 = __VLS_244.apply(void 0, __spreadArray([__assign({ show: (__VLS_ctx.showUrlModal), preset: "card", title: "通过 URL 下载" }, { style: {} })], __VLS_functionalComponentArgsRest(__VLS_244), false));
var __VLS_248 = __VLS_246.slots.default;
var __VLS_249;
/** @ts-ignore @type {typeof __VLS_components.nForm | typeof __VLS_components.NForm | typeof __VLS_components.nForm | typeof __VLS_components.NForm} */
nForm;
// @ts-ignore
var __VLS_250 = __VLS_asFunctionalComponent1(__VLS_249, new __VLS_249({
    ref: "urlFormRef",
    model: (__VLS_ctx.urlForm),
    labelPlacement: "left",
    labelWidth: "80",
}));
var __VLS_251 = __VLS_250.apply(void 0, __spreadArray([{
        ref: "urlFormRef",
        model: (__VLS_ctx.urlForm),
        labelPlacement: "left",
        labelWidth: "80",
    }], __VLS_functionalComponentArgsRest(__VLS_250), false));
var __VLS_254 = {};
var __VLS_256 = __VLS_252.slots.default;
var __VLS_257;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_258 = __VLS_asFunctionalComponent1(__VLS_257, new __VLS_257({
    label: "URL",
    path: "url",
    rule: ({ required: true, message: '请输入 URL' }),
}));
var __VLS_259 = __VLS_258.apply(void 0, __spreadArray([{
        label: "URL",
        path: "url",
        rule: ({ required: true, message: '请输入 URL' }),
    }], __VLS_functionalComponentArgsRest(__VLS_258), false));
var __VLS_262 = __VLS_260.slots.default;
var __VLS_263;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_264 = __VLS_asFunctionalComponent1(__VLS_263, new __VLS_263({
    value: (__VLS_ctx.urlForm.url),
    placeholder: "音乐 URL 或 ID",
}));
var __VLS_265 = __VLS_264.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.urlForm.url),
        placeholder: "音乐 URL 或 ID",
    }], __VLS_functionalComponentArgsRest(__VLS_264), false));
// @ts-ignore
[showUrlModal, urlForm, urlForm,];
var __VLS_260;
var __VLS_268;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_269 = __VLS_asFunctionalComponent1(__VLS_268, new __VLS_268({
    label: "来源",
    path: "source",
}));
var __VLS_270 = __VLS_269.apply(void 0, __spreadArray([{
        label: "来源",
        path: "source",
    }], __VLS_functionalComponentArgsRest(__VLS_269), false));
var __VLS_273 = __VLS_271.slots.default;
var __VLS_274;
/** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
nSelect;
// @ts-ignore
var __VLS_275 = __VLS_asFunctionalComponent1(__VLS_274, new __VLS_274({
    value: (__VLS_ctx.urlForm.source),
    options: (__VLS_ctx.sourceOptions),
    placeholder: "选择下载来源",
}));
var __VLS_276 = __VLS_275.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.urlForm.source),
        options: (__VLS_ctx.sourceOptions),
        placeholder: "选择下载来源",
    }], __VLS_functionalComponentArgsRest(__VLS_275), false));
// @ts-ignore
[sourceOptions, urlForm,];
var __VLS_271;
var __VLS_279;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_280 = __VLS_asFunctionalComponent1(__VLS_279, new __VLS_279({
    label: "音质",
    path: "quality",
}));
var __VLS_281 = __VLS_280.apply(void 0, __spreadArray([{
        label: "音质",
        path: "quality",
    }], __VLS_functionalComponentArgsRest(__VLS_280), false));
var __VLS_284 = __VLS_282.slots.default;
var __VLS_285;
/** @ts-ignore @type {typeof __VLS_components.nSelect | typeof __VLS_components.NSelect} */
nSelect;
// @ts-ignore
var __VLS_286 = __VLS_asFunctionalComponent1(__VLS_285, new __VLS_285({
    value: (__VLS_ctx.urlForm.quality),
    options: (__VLS_ctx.qualityOptions),
    placeholder: "选择音质",
}));
var __VLS_287 = __VLS_286.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.urlForm.quality),
        options: (__VLS_ctx.qualityOptions),
        placeholder: "选择音质",
    }], __VLS_functionalComponentArgsRest(__VLS_286), false));
// @ts-ignore
[qualityOptions, urlForm,];
var __VLS_282;
var __VLS_290;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_291 = __VLS_asFunctionalComponent1(__VLS_290, new __VLS_290({
    label: "标题",
    path: "title",
}));
var __VLS_292 = __VLS_291.apply(void 0, __spreadArray([{
        label: "标题",
        path: "title",
    }], __VLS_functionalComponentArgsRest(__VLS_291), false));
var __VLS_295 = __VLS_293.slots.default;
var __VLS_296;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_297 = __VLS_asFunctionalComponent1(__VLS_296, new __VLS_296({
    value: (__VLS_ctx.urlForm.title),
    placeholder: "可选，覆盖自动识别的标题",
}));
var __VLS_298 = __VLS_297.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.urlForm.title),
        placeholder: "可选，覆盖自动识别的标题",
    }], __VLS_functionalComponentArgsRest(__VLS_297), false));
// @ts-ignore
[urlForm,];
var __VLS_293;
var __VLS_301;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_302 = __VLS_asFunctionalComponent1(__VLS_301, new __VLS_301({
    label: "艺术家",
    path: "artist",
}));
var __VLS_303 = __VLS_302.apply(void 0, __spreadArray([{
        label: "艺术家",
        path: "artist",
    }], __VLS_functionalComponentArgsRest(__VLS_302), false));
var __VLS_306 = __VLS_304.slots.default;
var __VLS_307;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_308 = __VLS_asFunctionalComponent1(__VLS_307, new __VLS_307({
    value: (__VLS_ctx.urlForm.artist),
    placeholder: "可选，覆盖自动识别的艺术家",
}));
var __VLS_309 = __VLS_308.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.urlForm.artist),
        placeholder: "可选，覆盖自动识别的艺术家",
    }], __VLS_functionalComponentArgsRest(__VLS_308), false));
// @ts-ignore
[urlForm,];
var __VLS_304;
var __VLS_312;
/** @ts-ignore @type {typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem | typeof __VLS_components.nFormItem | typeof __VLS_components.NFormItem} */
nFormItem;
// @ts-ignore
var __VLS_313 = __VLS_asFunctionalComponent1(__VLS_312, new __VLS_312({
    label: "专辑",
    path: "album",
}));
var __VLS_314 = __VLS_313.apply(void 0, __spreadArray([{
        label: "专辑",
        path: "album",
    }], __VLS_functionalComponentArgsRest(__VLS_313), false));
var __VLS_317 = __VLS_315.slots.default;
var __VLS_318;
/** @ts-ignore @type {typeof __VLS_components.nInput | typeof __VLS_components.NInput} */
nInput;
// @ts-ignore
var __VLS_319 = __VLS_asFunctionalComponent1(__VLS_318, new __VLS_318({
    value: (__VLS_ctx.urlForm.album),
    placeholder: "可选，覆盖自动识别的专辑",
}));
var __VLS_320 = __VLS_319.apply(void 0, __spreadArray([{
        value: (__VLS_ctx.urlForm.album),
        placeholder: "可选，覆盖自动识别的专辑",
    }], __VLS_functionalComponentArgsRest(__VLS_319), false));
// @ts-ignore
[urlForm,];
var __VLS_315;
// @ts-ignore
[];
var __VLS_252;
{
    var __VLS_323 = __VLS_246.slots.footer;
    var __VLS_324 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nSpace | typeof __VLS_components.NSpace | typeof __VLS_components.nSpace | typeof __VLS_components.NSpace} */
    nSpace;
    // @ts-ignore
    var __VLS_325 = __VLS_asFunctionalComponent1(__VLS_324, new __VLS_324({
        justify: "end",
    }));
    var __VLS_326 = __VLS_325.apply(void 0, __spreadArray([{
            justify: "end",
        }], __VLS_functionalComponentArgsRest(__VLS_325), false));
    var __VLS_329 = __VLS_327.slots.default;
    var __VLS_330 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_331 = __VLS_asFunctionalComponent1(__VLS_330, new __VLS_330(__assign({ 'onClick': {} })));
    var __VLS_332 = __VLS_331.apply(void 0, __spreadArray([__assign({ 'onClick': {} })], __VLS_functionalComponentArgsRest(__VLS_331), false));
    var __VLS_335 = void 0;
    var __VLS_336 = ({ click: {} },
        { onClick: function () {
                var _a = [];
                for (var _i = 0; _i < arguments.length; _i++) {
                    _a[_i] = arguments[_i];
                }
                var $event = _a[0];
                __VLS_ctx.showUrlModal = false;
                // @ts-ignore
                [showUrlModal,];
            } });
    var __VLS_337 = __VLS_333.slots.default;
    // @ts-ignore
    [];
    var __VLS_333;
    var __VLS_334;
    var __VLS_338 = void 0;
    /** @ts-ignore @type {typeof __VLS_components.nButton | typeof __VLS_components.NButton | typeof __VLS_components.nButton | typeof __VLS_components.NButton} */
    nButton;
    // @ts-ignore
    var __VLS_339 = __VLS_asFunctionalComponent1(__VLS_338, new __VLS_338(__assign({ 'onClick': {} }, { type: "primary", loading: (__VLS_ctx.downloadingByUrl) })));
    var __VLS_340 = __VLS_339.apply(void 0, __spreadArray([__assign({ 'onClick': {} }, { type: "primary", loading: (__VLS_ctx.downloadingByUrl) })], __VLS_functionalComponentArgsRest(__VLS_339), false));
    var __VLS_343 = void 0;
    var __VLS_344 = ({ click: {} },
        { onClick: (__VLS_ctx.handleUrlDownload) });
    var __VLS_345 = __VLS_341.slots.default;
    // @ts-ignore
    [downloadingByUrl, handleUrlDownload,];
    var __VLS_341;
    var __VLS_342;
    // @ts-ignore
    [];
    var __VLS_327;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_246;
// @ts-ignore
var __VLS_174 = __VLS_173, __VLS_255 = __VLS_254;
// @ts-ignore
[];
var __VLS_export = (await Promise.resolve().then(function () { return require('vue'); })).defineComponent({});
exports.default = {};
