// 全局动画配置
export const animations = {
  // 页面过渡动画
  pageTransition: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
    transition: { duration: 0.3, ease: "easeInOut" }
  },

  // 卡片动画
  cardHover: {
    hover: { 
      y: -5, 
      scale: 1.02,
      transition: { duration: 0.2, ease: "easeOut" }
    },
    tap: { 
      scale: 0.98,
      transition: { duration: 0.1 }
    }
  },

  // 按钮动画
  buttonPress: {
    whileTap: { scale: 0.95 },
    whileHover: { scale: 1.05 },
    transition: { type: "spring", stiffness: 400, damping: 17 }
  },

  // 淡入动画
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5 }
  },

  // 从下方滑入
  slideInUp: {
    initial: { opacity: 0, y: 50 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6, ease: "easeOut" }
  },

  // 从左侧滑入
  slideInLeft: {
    initial: { opacity: 0, x: -50 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.6, ease: "easeOut" }
  },

  // 从右侧滑入
  slideInRight: {
    initial: { opacity: 0, x: 50 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.6, ease: "easeOut" }
  },

  // 缩放动画
  scaleIn: {
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.4, ease: "easeOut" }
  },

  // 弹性动画
  bounce: {
    animate: {
      y: [0, -10, 0],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },

  // 脉冲动画
  pulse: {
    animate: {
      scale: [1, 1.05, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },

  // 旋转动画
  rotate: {
    animate: {
      rotate: 360,
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "linear"
      }
    }
  },

  // 光效动画
  glow: {
    animate: {
      boxShadow: [
        "0 0 20px rgba(59, 130, 246, 0.3)",
        "0 0 40px rgba(59, 130, 246, 0.6)",
        "0 0 20px rgba(59, 130, 246, 0.3)"
      ],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },

  // 列表项动画
  listItem: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
    transition: { duration: 0.3 }
  },

  // 模态框动画
  modal: {
    overlay: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
      transition: { duration: 0.2 }
    },
    content: {
      initial: { opacity: 0, scale: 0.8, y: 50 },
      animate: { opacity: 1, scale: 1, y: 0 },
      exit: { opacity: 0, scale: 0.8, y: 50 },
      transition: { type: "spring", damping: 25, stiffness: 300 }
    }
  },

  // 通知动画
  notification: {
    initial: { opacity: 0, x: 300, scale: 0.8 },
    animate: { opacity: 1, x: 0, scale: 1 },
    exit: { opacity: 0, x: 300, scale: 0.8 },
    transition: { type: "spring", damping: 20, stiffness: 300 }
  }
};

// 延迟动画工具函数
export const staggerChildren = (delayPerChild = 0.1) => ({
  animate: {
    transition: {
      staggerChildren: delayPerChild
    }
  }
});

// 创建延迟动画
export const createDelayedAnimation = (baseAnimation: any, delay: number) => ({
  ...baseAnimation,
  transition: {
    ...baseAnimation.transition,
    delay
  }
});

// 响应式动画配置
export const responsiveAnimations = {
  // 移动端减少动画
  mobile: {
    transition: { duration: 0.2 },
    hover: {},
    tap: { scale: 0.98 }
  },
  // 桌面端完整动画
  desktop: {
    transition: { duration: 0.3 },
    hover: { y: -5, scale: 1.02 },
    tap: { scale: 0.98 }
  }
};