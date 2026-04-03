import React from 'react';
import { motion } from 'framer-motion';
import { useResponsive, useResponsiveValue, BreakpointKey } from '../../hooks/useResponsive';
import { staggerChildren } from '../../utils/animations';

export interface ResponsiveGridProps {
  children: React.ReactNode;
  columns?: Partial<Record<BreakpointKey, number>>;
  gap?: Partial<Record<BreakpointKey, number>>;
  className?: string;
  animate?: boolean;
  minItemWidth?: number;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 5 },
  gap = { xs: 16, sm: 20, md: 24, lg: 28, xl: 32 },
  className = '',
  animate = true,
  minItemWidth = 200
}) => {
  const { width } = useResponsive();
  
  // 响应式列数
  const responsiveColumns = useResponsiveValue(columns, 1);
  
  // 响应式间距
  const responsiveGap = useResponsiveValue(gap, 16);
  
  // 自动计算列数（基于最小宽度）
  const autoColumns = Math.floor((width - responsiveGap) / (minItemWidth + responsiveGap));
  const finalColumns = Math.min(responsiveColumns, autoColumns);

  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `repeat(${finalColumns}, 1fr)`,
    gap: `${responsiveGap}px`,
    width: '100%'
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: staggerChildren(0.1)
    }
  };

  const itemVariants: import('framer-motion').Variants = {
    hidden: { 
      opacity: 0, 
      y: 20,
      scale: 0.95
    },
    visible: { 
      opacity: 1, 
      y: 0,
      scale: 1,
      transition: {
        duration: 0.4,
        ease: [0.4, 0, 0.2, 1]
      }
    }
  };

  if (animate) {
    return (
      <motion.div
        className={className}
        style={gridStyle}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {React.Children.map(children, (child, index) => (
          <motion.div
            key={index}
            variants={itemVariants}
            layout
          >
            {child}
          </motion.div>
        ))}
      </motion.div>
    );
  }

  return (
    <div className={className} style={gridStyle}>
      {children}
    </div>
  );
};

// 响应式Flex布局组件
export interface ResponsiveFlexProps {
  children: React.ReactNode;
  direction?: Partial<Record<BreakpointKey, 'row' | 'column'>>;
  justify?: Partial<Record<BreakpointKey, 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly'>>;
  align?: Partial<Record<BreakpointKey, 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline'>>;
  wrap?: Partial<Record<BreakpointKey, 'nowrap' | 'wrap' | 'wrap-reverse'>>;
  gap?: Partial<Record<BreakpointKey, number>>;
  className?: string;
  animate?: boolean;
}

export const ResponsiveFlex: React.FC<ResponsiveFlexProps> = ({
  children,
  direction = { xs: 'column', md: 'row' },
  justify = { xs: 'flex-start' },
  align = { xs: 'stretch' },
  wrap = { xs: 'wrap' },
  gap = { xs: 16, md: 24 },
  className = '',
  animate = true
}) => {
  const responsiveDirection = useResponsiveValue(direction, 'row');
  const responsiveJustify = useResponsiveValue(justify, 'flex-start');
  const responsiveAlign = useResponsiveValue(align, 'stretch');
  const responsiveWrap = useResponsiveValue(wrap, 'wrap');
  const responsiveGap = useResponsiveValue(gap, 16);

  const flexStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: responsiveDirection,
    justifyContent: responsiveJustify,
    alignItems: responsiveAlign,
    flexWrap: responsiveWrap,
    gap: `${responsiveGap}px`
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: staggerChildren(0.1)
    }
  };

  const itemVariants: import('framer-motion').Variants = {
    hidden: { 
      opacity: 0, 
      x: responsiveDirection === 'row' ? -20 : 0,
      y: responsiveDirection === 'column' ? -20 : 0
    },
    visible: { 
      opacity: 1, 
      x: 0,
      y: 0,
      transition: {
        duration: 0.4,
        ease: [0.4, 0, 0.2, 1]
      }
    }
  };

  if (animate) {
    return (
      <motion.div
        className={className}
        style={flexStyle}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {React.Children.map(children, (child, index) => (
          <motion.div
            key={index}
            variants={itemVariants}
            layout
          >
            {child}
          </motion.div>
        ))}
      </motion.div>
    );
  }

  return (
    <div className={className} style={flexStyle}>
      {children}
    </div>
  );
};

// 响应式容器组件
export interface ResponsiveContainerProps {
  children: React.ReactNode;
  maxWidth?: Partial<Record<BreakpointKey, number | string>>;
  padding?: Partial<Record<BreakpointKey, number>>;
  className?: string;
}

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  maxWidth = { xs: '100%', sm: 640, md: 768, lg: 1024, xl: 1280, '2xl': 1536 },
  padding = { xs: 16, sm: 24, md: 32, lg: 40, xl: 48 },
  className = ''
}) => {
  const responsiveMaxWidth = useResponsiveValue(maxWidth, 1024);
  const responsivePadding = useResponsiveValue(padding, 16);

  const containerStyle: React.CSSProperties = {
    maxWidth: typeof responsiveMaxWidth === 'number' ? `${responsiveMaxWidth}px` : responsiveMaxWidth,
    margin: '0 auto',
    padding: `0 ${responsivePadding}px`,
    width: '100%'
  };

  return (
    <div className={className} style={containerStyle}>
      {children}
    </div>
  );
};