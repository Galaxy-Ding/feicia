# REFERENCE_HIG.md - Apple iOS 26 设计语言参考

## Apple Human Interface Guidelines - iOS 26 Liquid Glass 核心视觉令牌

> **重要更新**：本文档基于iOS 26 (2025 WWDC)的Liquid Glass设计语言，这是自iOS 7以来最大的视觉重新设计。
> 适用平台：iOS 26、iPadOS 26、macOS Tahoe 26、watchOS 26、tvOS 26、visionOS 26

---

## 核心视觉令牌（CSS Variables - 必须使用）
```css
:root {
    /* ============================================
       iOS 26 Liquid Glass 材质系统 - NEW!
       ============================================ */
    
    /* 玻璃材质基础 */
    --glass-clear: rgba(255, 255, 255, 0.72);           /* 清晰玻璃（亮模式） */
    --glass-tinted: rgba(242, 242, 247, 0.78);          /* 着色玻璃 */
    --glass-frosted: rgba(250, 250, 250, 0.82);         /* 磨砂玻璃 */
    --glass-dark: rgba(28, 28, 30, 0.72);               /* 暗色玻璃（暗模式） */
    --glass-dark-tinted: rgba(44, 44, 46, 0.78);        /* 暗色着色玻璃 */
    
    /* 玻璃模糊效果 */
    --glass-blur-light: blur(20px);                      /* 轻度模糊 */
    --glass-blur-medium: blur(40px);                     /* 中度模糊 */
    --glass-blur-heavy: blur(60px);                      /* 重度模糊 */
    
    /* 玻璃边框 */
    --glass-border: 1px solid rgba(255, 255, 255, 0.18); /* 玻璃边缘高光 */
    --glass-border-dark: 1px solid rgba(255, 255, 255, 0.08); /* 暗模式边缘 */
    
    /* 玻璃光泽效果 */
    --glass-shine: linear-gradient(135deg, 
                   rgba(255, 255, 255, 0.3) 0%, 
                   rgba(255, 255, 255, 0) 50%);          /* 玻璃反光 */
    
    
    /* ============================================
       Apple 系统色彩 - iOS 标准色板
       ============================================ */
    
    /* 主要系统色 */
    --system-blue: #007AFF;                              /* Apple标准蓝 */
    --system-blue-hover: #0051D5;                        /* 悬停态（深20%） */
    --system-blue-active: #004BB8;                       /* 按下态（深30%） */
    --system-green: #34C759;                             /* 系统绿 */
    --system-red: #FF3B30;                               /* 系统红 */
    --system-orange: #FF9500;                            /* 系统橙 */
    --system-yellow: #FFCC00;                            /* 系统黄 */
    --system-purple: #AF52DE;                            /* 系统紫 */
    --system-pink: #FF2D55;                              /* 系统粉 */
    --system-teal: #5AC8FA;                              /* 系统青 */
    --system-indigo: #5856D6;                            /* 系统靛 */
    --system-cyan: #32ADE6;                              /* 系统青蓝 */
    --system-mint: #00C7BE;                              /* 系统薄荷 */
    --system-brown: #A2845E;                             /* 系统棕 */
    
    /* 灰度系统 */
    --system-gray: #8E8E93;                              /* 系统灰 */
    --system-gray2: #AEAEB2;                             /* 系统灰2 */
    --system-gray3: #C7C7CC;                             /* 系统灰3 */
    --system-gray4: #D1D1D6;                             /* 系统灰4 */
    --system-gray5: #E5E5EA;                             /* 系统灰5 */
    --system-gray6: #F2F2F7;                             /* 系统灰6 */
    
    
    /* ============================================
       语义化色彩 - 支持明暗模式自动切换
       ============================================ */
    
    /* 文字颜色层级 */
    --label: #000000;                                    /* 主要文字（暗模式：#FFFFFF） */
    --secondary-label: rgba(60, 60, 67, 0.60);          /* 次要文字（暗模式：rgba(235, 235, 245, 0.60)） */
    --tertiary-label: rgba(60, 60, 67, 0.30);           /* 辅助文字（暗模式：rgba(235, 235, 245, 0.30)） */
    --quaternary-label: rgba(60, 60, 67, 0.18);         /* 占位文字（暗模式：rgba(235, 235, 245, 0.18)） */
    --placeholder-text: rgba(60, 60, 67, 0.30);         /* 输入框占位符 */
    
    /* 背景系统 - Stack 1（标准背景） */
    --system-background: #FFFFFF;                        /* 系统主背景（暗模式：#000000） */
    --secondary-system-background: #F2F2F7;              /* 二级背景（暗模式：#1C1C1E） */
    --tertiary-system-background: #FFFFFF;               /* 三级背景（暗模式：#2C2C2E） */
    
    /* 背景系统 - Stack 2（分组背景） */
    --system-grouped-background: #F2F2F7;                /* 分组列表背景（暗模式：#000000） */
    --secondary-grouped-background: #FFFFFF;             /* 分组内容背景（暗模式：#1C1C1E） */
    --tertiary-grouped-background: #F2F2F7;              /* 三级分组背景（暗模式：#2C2C2E） */
    
    /* 填充色系统 - iOS 26更新 */
    --system-fill: rgba(120, 120, 128, 0.20);           /* 薄形状填充（slider track） */
    --secondary-system-fill: rgba(120, 120, 128, 0.16); /* 中等形状填充（switch） */
    --tertiary-system-fill: rgba(118, 118, 128, 0.12);  /* 大型形状填充（input, button） */
    --quaternary-system-fill: rgba(116, 116, 128, 0.08); /* 超大区域填充（expanded cells） */
    
    /* 分隔线和边框 */
    --separator: rgba(60, 60, 67, 0.29);                /* 半透明分隔线（暗模式：rgba(84, 84, 88, 0.60)） */
    --opaque-separator: #C6C6C8;                         /* 不透明分隔线（暗模式：#38383A） */
    --separator-non-opaque: rgba(60, 60, 67, 0.36);     /* iOS 26新增 */
    
    /* 链接色 */
    --link: #007AFF;                                     /* 链接颜色（与system-blue一致） */
    --link-hover: #0051D5;                               /* 链接悬停 */
    
    
    /* ============================================
       布局系统 - 基于Apple规范
       ============================================ */
    
    /* 容器和边距 */
    --container-max: 1194px;                             /* 最大容器宽度（iPad Pro 12.9"） */
    --container-standard: 375px;                         /* iPhone标准宽度 */
    --container-large: 430px;                            /* iPhone Pro Max宽度 */
    
    /* 安全区域 */
    --safe-area: 20px;                                   /* 标准安全边距 */
    --safe-area-compact: 16px;                           /* 紧凑安全边距 */
    --safe-area-mini: 8px;                               /* 最小安全边距 */
    
    /* 栅格系统 */
    --grid-unit: 8px;                                    /* iOS标准栅格单位（必须遵守） */
    
    
    /* ============================================
       SF Pro 字体系统
       ============================================ */
    
    /* 字体族 */
    --font-family: -apple-system, BlinkMacSystemFont, 
                   'PingFang SC', 'SF Pro Text', 'SF Pro Display', 
                   'Helvetica Neue', sans-serif;
    --font-family-monospace: 'SF Mono', ui-monospace, 
                             'Cascadia Code', 'Source Code Pro', 
                             Menlo, Consolas, monospace;
    
    /* 字号系统（iOS Dynamic Type） */
    --text-xs: 11pt;                                     /* 极小字（Caption 2） */
    --text-sm: 13pt;                                     /* 小字（Caption 1, Footnote） */
    --text-base: 17pt;                                   /* 正文（Body - iOS默认）⭐ */
    --text-md: 19pt;                                     /* 中标题（Callout） */
    --text-lg: 20pt;                                     /* 副标题（Headline） */
    --text-xl: 22pt;                                     /* 标题（Title 3） */
    --text-2xl: 28pt;                                    /* 大标题（Title 2） */
    --text-3xl: 34pt;                                    /* 超大标题（Title 1） */
    --text-4xl: 48pt;                                    /* Large Title（iOS特有） */
    
    /* 字重系统 */
    --font-weight-regular: 400;                          /* Regular */
    --font-weight-medium: 500;                           /* Medium（iOS 26新增） */
    --font-weight-semibold: 600;                         /* Semibold（常用）⭐ */
    --font-weight-bold: 700;                             /* Bold */
    --font-weight-heavy: 800;                            /* Heavy */
    --font-weight-black: 900;                            /* Black */
    
    /* 行高系统 */
    --line-height-tight: 1.2;                            /* 紧凑行高（标题） */
    --line-height-base: 1.4;                             /* 基础行高（正文）⭐ */
    --line-height-relaxed: 1.6;                          /* 宽松行高（长文本） */
    
    /* 字符间距 */
    --letter-spacing-tight: -0.02em;                     /* 紧凑（大标题） */
    --letter-spacing-normal: 0;                          /* 正常 */
    --letter-spacing-wide: 0.02em;                       /* 宽松（小字） */
    
    
    /* ============================================
       间距系统（8pt栅格 - 必须严格遵守）
       ============================================ */
    
    --spacing-0: 0px;                                    /* 无间距 */
    --spacing-1: 4px;                                    /* 0.5x（极小）*/
    --spacing-2: 8px;                                    /* 1x（最小间距）⭐ */
    --spacing-3: 12px;                                   /* 1.5x（小间距） */
    --spacing-4: 16px;                                   /* 2x（中间距）⭐ */
    --spacing-5: 20px;                                   /* 2.5x（大间距）⭐ */
    --spacing-6: 24px;                                   /* 3x（超大间距） */
    --spacing-8: 32px;                                   /* 4x（区块间距） */
    --spacing-10: 40px;                                  /* 5x */
    --spacing-12: 48px;                                  /* 6x */
    --spacing-16: 64px;                                  /* 8x（巨大间距） */
    
    
    /* ============================================
       圆角系统 - iOS 26 Liquid Glass更新
       ============================================ */
    
    /* 标准圆角（增加了圆润度） */
    --radius-xs: 6px;                                    /* 极小圆角 */
    --radius-sm: 8px;                                    /* 小圆角（Badge）⭐ */
    --radius-md: 12px;                                   /* 标准圆角（Button）⭐ */
    --radius-lg: 16px;                                   /* 大圆角（Card）⭐ */
    --radius-xl: 20px;                                   /* 超大圆角（Sheet） */
    --radius-2xl: 24px;                                  /* 巨型圆角（Modal） */
    --radius-3xl: 32px;                                  /* iOS 26新增 */
    
    /* 特殊圆角 */
    --radius-continuous: 42%;                            /* 连续曲线圆角（iOS标志性）⭐ */
    --radius-circle: 50%;                                /* 完整圆形 */
    --radius-pill: 999px;                                /* 胶囊形 */
    
    
    /* ============================================
       阴影系统 - iOS 26 Liquid Glass 玻璃阴影
       ============================================ */
    
    /* 标准阴影 - 更轻量 */
    --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);         /* 极轻阴影 */
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);         /* 轻微阴影⭐ */
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.10);        /* 中等阴影 */
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);        /* 大阴影（Modal） */
    --shadow-xl: 0 12px 40px rgba(0, 0, 0, 0.15);       /* 超大阴影 */
    
    /* 玻璃阴影 - iOS 26特有 */
    --shadow-glass-sm: 0 2px 10px rgba(0, 0, 0, 0.08),
                       0 0 1px rgba(0, 0, 0, 0.12),
                       inset 0 1px 0 rgba(255, 255, 255, 0.3); /* 玻璃轻阴影⭐ */
    
    --shadow-glass-md: 0 4px 20px rgba(0, 0, 0, 0.12),
                       0 0 2px rgba(0, 0, 0, 0.15),
                       inset 0 1px 0 rgba(255, 255, 255, 0.3); /* 玻璃中阴影⭐ */
    
    --shadow-glass-lg: 0 10px 40px rgba(0, 0, 0, 0.15),
                       0 0 3px rgba(0, 0, 0, 0.20),
                       inset 0 1px 0 rgba(255, 255, 255, 0.3); /* 玻璃大阴影 */
    
    /* 浮动阴影 - iOS 26浮动UI */
    --shadow-floating: 0 8px 32px rgba(0, 0, 0, 0.12),
                       0 0 2px rgba(0, 0, 0, 0.08);     /* 浮动元素阴影 */
    
    
    /* ============================================
       动效系统 - iOS 26流畅动画
       ============================================ */
    
    /* 持续时间 */
    --duration-instant: 100ms;                           /* 即时反馈 */
    --duration-fast: 200ms;                              /* 快速动画⭐ */
    --duration-base: 350ms;                              /* 基础动画⭐ */
    --duration-slow: 500ms;                              /* 慢速动画 */
    --duration-slower: 700ms;                            /* 更慢动画 */
    
    /* 缓动曲线 - Apple标准 */
    --ease-in-out: cubic-bezier(0.25, 0.1, 0.25, 1);    /* 标准缓动 */
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);          /* 出场缓动 */
    --ease-in: cubic-bezier(0.4, 0, 1, 1);              /* 入场缓动 */
    
    /* iOS 26特有缓动 */
    --ease-spring: cubic-bezier(0.32, 0.72, 0, 1);      /* 弹簧效果⭐ */
    --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55); /* 弹跳效果 */
    --ease-glass: cubic-bezier(0.25, 0.46, 0.45, 0.94); /* 玻璃过渡⭐ */
    
    /* 完整过渡 */
    --transition-fast: 200ms var(--ease-in-out);
    --transition-base: 350ms var(--ease-in-out);
    --transition-spring: 450ms var(--ease-spring);      /* 推荐⭐ */
    --transition-glass: 350ms var(--ease-glass);        /* 玻璃效果⭐ */
    
    
    /* ============================================
       Z-index 层级系统
       ============================================ */
    
    --z-base: 0;                                         /* 基础层 */
    --z-dropdown: 1000;                                  /* 下拉菜单 */
    --z-sticky: 1020;                                    /* 吸顶元素 */
    --z-fixed: 1030;                                     /* 固定元素 */
    --z-modal-backdrop: 1040;                            /* 模态背景 */
    --z-modal: 1050;                                     /* 模态框 */
    --z-popover: 1060;                                   /* 弹出层 */
    --z-tooltip: 1070;                                   /* 提示层 */
    --z-notification: 1080;                              /* 通知 */
    
    
    /* ============================================
       iOS 26 组件特定令牌
       ============================================ */
    
    /* Tab Bar */
    --tabbar-height: 49px;                               /* 标准Tab Bar高度 */
    --tabbar-height-safe: calc(49px + env(safe-area-inset-bottom)); /* 含安全区 */
    --tabbar-icon-size: 28px;                            /* 图标尺寸 */
    
    /* Navigation Bar */
    --navbar-height: 44px;                               /* 标准导航栏高度 */
    --navbar-height-large: 96px;                         /* 大标题导航栏 */
    
    /* Button */
    --button-height-sm: 28px;                            /* 小按钮 */
    --button-height-md: 44px;                            /* 标准按钮⭐ */
    --button-height-lg: 50px;                            /* 大按钮 */
    --button-padding-x: 16px;                            /* 按钮水平内边距 */
    
    /* Input */
    --input-height: 44px;                                /* 标准输入框高度 */
    --input-padding-x: 12px;                             /* 输入框内边距 */
    
    /* Card */
    --card-padding: 16px;                                /* 卡片内边距⭐ */
    --card-padding-lg: 20px;                             /* 大卡片内边距 */
    
    /* List */
    --list-item-height: 44px;                            /* 标准列表项高度⭐ */
    --list-item-height-lg: 56px;                         /* 大列表项 */
    
    
    /* ============================================
       响应式断点
       ============================================ */
    
    --breakpoint-xs: 320px;                              /* iPhone SE */
    --breakpoint-sm: 375px;                              /* iPhone标准 */
    --breakpoint-md: 390px;                              /* iPhone 14/15 */
    --breakpoint-lg: 430px;                              /* iPhone Pro Max */
    --breakpoint-xl: 744px;                              /* iPad Mini */
    --breakpoint-2xl: 1024px;                            /* iPad */
    --breakpoint-3xl: 1366px;                            /* iPad Pro */
}
```

---

## 🎨 iOS 26 Liquid Glass设计原则

### 1. 清晰性（Clarity）- 增强版
- **玻璃质感优先**：UI元素应具有半透明的玻璃质感
- **内容至上**：界面应"透"出背后的内容
- **视觉层次**：使用深度和模糊创建清晰的层级

### 2. 深度（Depth）- Liquid Glass核心
- **多层玻璃**：通过多层半透明材质创建深度
- **折射效果**：模拟真实玻璃的光学特性
- **浮动UI**：元素不再固定在边缘，而是浮动显示

### 3. 流畅性（Fluidity）- iOS 26新增
- **动态响应**：UI元素响应内容、动作和环境光
- **平滑过渡**：所有交互都应有流畅的动画
- **连续性**：跨设备的一致体验

### 4. 尊重（Deference）
- **轻量设计**：最小化视觉干扰
- **触觉反馈**：适当的Haptic Feedback
- **可访问性**：支持Dynamic Type和VoiceOver

---

## 📐 使用指南

### 色彩使用规范
```css
/* ✅ 正确 - 使用语义化颜色 */
.text { color: var(--label); }
.secondary-text { color: var(--secondary-label); }
.button { background: var(--system-blue); }

/* ❌ 错误 - 不要硬编码颜色 */
.text { color: #000000; }
.button { background: #007AFF; }
```

### 玻璃效果实现
```css
/* iOS 26 Liquid Glass标准实现 */
.glass-card {
    background: var(--glass-clear);
    backdrop-filter: var(--glass-blur-light);
    -webkit-backdrop-filter: var(--glass-blur-light);
    border: var(--glass-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-glass-md);
    
    /* 添加玻璃反光 */
    position: relative;
}

.glass-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 50%;
    background: var(--glass-shine);
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    pointer-events: none;
}
```

### 字体规范
- **< 20pt**：使用SF Pro Text
- **≥ 20pt**：使用SF Pro Display
- **中文**：优先使用PingFang SC（苹方）
- **等宽**：使用SF Mono

### 间距规范
```css
/* 必须使用8pt栅格的倍数 */
.spacing-correct {
    padding: var(--spacing-4);  /* 16px = 8 × 2 ✅ */
    margin: var(--spacing-5);   /* 20px = 8 × 2.5 ✅ */
}

.spacing-wrong {
    padding: 15px;  /* ❌ 不是8的倍数 */
    margin: 18px;   /* ❌ 不是8的倍数 */
}
```

### 圆角规范
```css
/* 根据元素大小选择合适的圆角 */
.badge { border-radius: var(--radius-sm); }      /* 8px */
.button { border-radius: var(--radius-md); }     /* 12px */
.card { border-radius: var(--radius-lg); }       /* 16px */
.modal { border-radius: var(--radius-2xl); }     /* 24px */

/* App图标使用连续曲线圆角 */
.app-icon { border-radius: var(--radius-continuous); } /* 42% */
```

### 动效规范
```css
/* 推荐使用弹簧动画 */
.interactive-element {
    transition: transform var(--transition-spring),
                opacity var(--transition-fast);
}

/* 玻璃效果使用专用缓动 */
.glass-element {
    transition: backdrop-filter var(--transition-glass),
                background var(--transition-glass);
}
```

---

## 🎯 组件示例

### Liquid Glass卡片
```css
.ios26-card {
    background: var(--glass-clear);
    backdrop-filter: var(--glass-blur-light);
    border: var(--glass-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-glass-md);
    padding: var(--spacing-4);
    transition: all var(--transition-spring);
}

.ios26-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-glass-lg);
}
```

### iOS 26按钮
```css
.ios26-button {
    height: var(--button-height-md);
    padding: 0 var(--button-padding-x);
    background: var(--system-blue);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    font-weight: var(--font-weight-semibold);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-spring);
}

.ios26-button:active {
    transform: scale(0.96);
    box-shadow: var(--shadow-xs);
}
```

### 浮动导航栏（iOS 26特性）
```css
.ios26-navbar {
    position: fixed;
    top: var(--spacing-4);
    left: var(--spacing-4);
    right: var(--spacing-4);
    height: var(--navbar-height);
    background: var(--glass-frosted);
    backdrop-filter: var(--glass-blur-medium);
    border: var(--glass-border);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-floating);
    z-index: var(--z-sticky);
}
```

---

## 📱 适配iOS 26的checklist

- [ ] 所有卡片使用Liquid Glass材质
- [ ] 移除所有重阴影，改用玻璃阴影
- [ ] 更新圆角到iOS 26标准（更圆润）
- [ ] 导航栏改为浮动式设计
- [ ] 使用语义化颜色，支持明暗模式
- [ ] 所有间距遵循8pt栅格
- [ ] 动画使用弹簧缓动曲线
- [ ] 字体使用SF Pro / PingFang SC
- [ ] 支持Dynamic Type
- [ ] 添加适当的Haptic Feedback
- [ ] 确保backdrop-filter支持

---

## 🌗 明暗模式支持
```css
/* 使用CSS媒体查询自动切换 */
@media (prefers-color-scheme: dark) {
    :root {
        --label: #FFFFFF;
        --secondary-label: rgba(235, 235, 245, 0.60);
        --system-background: #000000;
        --secondary-system-background: #1C1C1E;
        --glass-clear: var(--glass-dark);
        --glass-border: var(--glass-border-dark);
        /* ... 其他暗模式变量 */
    }
}
```

---

## 📚 参考资源

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [iOS 26 Design Resources](https://developer.apple.com/design/resources/)
- [SF Symbols 6](https://developer.apple.com/sf-symbols/)
- [Apple Developer Documentation](https://developer.apple.com/documentation/)

---

**版本信息**
- 文档版本：2.0
- 更新日期：2025年10月
- 适用系统：iOS 26+, iPadOS 26+, macOS Tahoe 26+
- 设计语言：Liquid Glass

**注意事项**
- iOS 27将强制要求Liquid Glass设计，传统设计将不再支持
- 本文档持续更新，请关注Apple WWDC最新发布
- 建议配合Figma iOS 26 UI Kit使用