import React, { useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useVirtualScroll } from '../../hooks/usePerformance';
import { useResponsive } from '../../hooks/useResponsive';

export interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T, index: number) => string | number;
  className?: string;
  overscan?: number;
  loading?: boolean;
  loadingComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  onEndReached?: () => void;
  onEndReachedThreshold?: number;
  animate?: boolean;
}

export const VirtualList = <T,>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  keyExtractor,
  className = '',
  overscan = 5,
  loading = false,
  loadingComponent,
  emptyComponent,
  onEndReached,
  onEndReachedThreshold = 0.8,
  animate = true
}: VirtualListProps<T>) => {
  const { isMobile } = useResponsive();
  
  const {
    visibleItems,
    totalHeight,
    handleScroll,
    containerProps
  } = useVirtualScroll(items, {
    itemHeight,
    containerHeight,
    overscan: isMobile ? 3 : overscan // 移动端减少预渲染项目
  });

  // 检测是否接近底部
  const handleScrollWithEndReached = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    handleScroll(e);
    
    if (onEndReached) {
      const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
      const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
      
      if (scrollPercentage >= onEndReachedThreshold) {
        onEndReached();
      }
    }
  }, [handleScroll, onEndReached, onEndReachedThreshold]);

  const itemVariants: import('framer-motion').Variants = {
    hidden: { 
      opacity: 0, 
      x: -20,
      scale: 0.95
    },
    visible: { 
      opacity: 1, 
      x: 0,
      scale: 1,
      transition: {
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1]
      }
    },
    exit: {
      opacity: 0,
      x: 20,
      scale: 0.95,
      transition: {
        duration: 0.2
      }
    }
  };

  // 空状态
  if (items.length === 0 && !loading) {
    return (
      <div 
        className={`flex items-center justify-center ${className}`}
        style={{ height: containerHeight }}
      >
        {emptyComponent || (
          <div className="text-center text-gray-500">
            <div className="text-4xl mb-4">📋</div>
            <div className="text-lg font-medium">暂无数据</div>
            <div className="text-sm">列表为空</div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={className}>
      <div
        {...containerProps}
        onScroll={handleScrollWithEndReached}
        className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100"
      >
        <div style={{ height: totalHeight, position: 'relative' }}>
          <AnimatePresence mode="popLayout">
            {visibleItems.map(({ item, index, style }) => (
              <motion.div
                key={keyExtractor(item, index)}
                style={style}
                variants={animate ? itemVariants : undefined}
                initial={animate ? "hidden" : undefined}
                animate={animate ? "visible" : undefined}
                exit={animate ? "exit" : undefined}
                layout={animate}
                className="flex items-center"
              >
                {renderItem(item, index)}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
        
        {/* 加载指示器 */}
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-center py-4"
          >
            {loadingComponent || (
              <div className="flex items-center space-x-2 text-gray-500">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
                <span>加载中...</span>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
};

// 虚拟化表格组件
export interface VirtualTableColumn<T> {
  key: string;
  title: string;
  width?: number;
  minWidth?: number;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  dataIndex?: keyof T;
  align?: 'left' | 'center' | 'right';
  fixed?: 'left' | 'right';
  sortable?: boolean;
}

export interface VirtualTableProps<T> {
  columns: VirtualTableColumn<T>[];
  dataSource: T[];
  rowHeight?: number;
  containerHeight: number;
  rowKey: keyof T | ((record: T) => string | number);
  className?: string;
  headerClassName?: string;
  rowClassName?: string | ((record: T, index: number) => string);
  onRow?: (record: T, index: number) => React.HTMLAttributes<HTMLDivElement>;
  loading?: boolean;
  animate?: boolean;
}

export const VirtualTable = <T extends Record<string, any>>({
  columns,
  dataSource,
  rowHeight = 48,
  containerHeight,
  rowKey,
  className = '',
  headerClassName = '',
  rowClassName = '',
  onRow,
  loading = false,
  animate = true
}: VirtualTableProps<T>) => {
  const { isMobile } = useResponsive();

  const getRowKey = useCallback((record: T, index: number) => {
    return typeof rowKey === 'function' ? rowKey(record) : record[rowKey];
  }, [rowKey]);

  const renderRow = useCallback((record: T, index: number) => {
    const rowProps = onRow?.(record, index) || {};
    const className = typeof rowClassName === 'function' 
      ? rowClassName(record, index) 
      : rowClassName;

    return (
      <div
        {...rowProps}
        className={`flex border-b border-gray-200 hover:bg-gray-50 transition-colors ${className}`}
        style={{ height: rowHeight }}
      >
        {columns.map((column, colIndex) => {
          const value = column.dataIndex ? record[column.dataIndex] : undefined;
          const content = column.render 
            ? column.render(value, record, index)
            : value;

          return (
            <div
              key={column.key}
              className={`flex items-center px-4 ${
                column.align === 'center' ? 'justify-center' :
                column.align === 'right' ? 'justify-end' : 'justify-start'
              }`}
              style={{
                width: column.width || `${100 / columns.length}%`,
                minWidth: column.minWidth || 100
              }}
            >
              {content}
            </div>
          );
        })}
      </div>
    );
  }, [columns, rowHeight, rowClassName, onRow]);

  // 表头
  const tableHeader = useMemo(() => (
    <div className={`flex bg-gray-50 border-b-2 border-gray-200 font-medium ${headerClassName}`}>
      {columns.map((column) => (
        <div
          key={column.key}
          className={`flex items-center px-4 py-3 ${
            column.align === 'center' ? 'justify-center' :
            column.align === 'right' ? 'justify-end' : 'justify-start'
          }`}
          style={{
            width: column.width || `${100 / columns.length}%`,
            minWidth: column.minWidth || 100
          }}
        >
          {column.title}
        </div>
      ))}
    </div>
  ), [columns, headerClassName]);

  return (
    <div className={`border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {tableHeader}
      <VirtualList
        items={dataSource}
        itemHeight={rowHeight}
        containerHeight={containerHeight - 48} // 减去表头高度
        renderItem={renderRow}
        keyExtractor={getRowKey}
        loading={loading}
        animate={animate}
        overscan={isMobile ? 3 : 5}
      />
    </div>
  );
};