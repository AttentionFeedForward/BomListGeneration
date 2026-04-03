import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

export interface InputProps {
  label?: string;
  placeholder?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'search';
  value?: string;
  onChange?: (value: string) => void;
  icon?: LucideIcon;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

const Input: React.FC<InputProps> = ({
  label,
  placeholder,
  type = 'text',
  value,
  onChange,
  icon: Icon,
  error,
  disabled = false,
  required = false,
  className = ''
}) => {
  const [focused, setFocused] = useState(false);
  const [internalValue, setInternalValue] = useState(value || '');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInternalValue(newValue);
    onChange?.(newValue);
  };

  const currentValue = value !== undefined ? value : internalValue;

  return (
    <div className={`relative ${className}`}>
      {/* 标签 */}
      {label && (
        <motion.label
          className="block text-sm font-medium text-gray-300 mb-2"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </motion.label>
      )}

      {/* 输入框容器 */}
      <motion.div
        className={`relative rounded-lg transition-all duration-300 ${
          focused 
            ? 'ring-2 ring-blue-400/50 ring-offset-2 ring-offset-transparent' 
            : ''
        } ${
          error 
            ? 'ring-2 ring-red-400/50 ring-offset-2 ring-offset-transparent' 
            : ''
        }`}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        {/* 背景光效 */}
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-600/10 rounded-lg opacity-0"
          animate={{ opacity: focused ? 1 : 0 }}
          transition={{ duration: 0.3 }}
        />

        {/* 图标 */}
        {Icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 z-10">
            <Icon 
              size={18} 
              className={`transition-colors duration-300 ${
                focused ? 'text-blue-400' : 'text-gray-400'
              }`} 
            />
          </div>
        )}

        {/* 输入框 */}
        <input
          type={type}
          placeholder={placeholder}
          value={currentValue}
          onChange={handleChange}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          disabled={disabled}
          className={`
            relative w-full px-4 py-3 bg-black/20 border border-white/20 rounded-lg
            text-white placeholder-gray-400 backdrop-blur-sm
            focus:outline-none focus:border-blue-400/50
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-all duration-300
            ${Icon ? 'pl-11' : ''}
            ${error ? 'border-red-400/50' : ''}
          `}
        />

        {/* 底部光线效果 */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-400 to-purple-600 rounded-full"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: focused ? 1 : 0 }}
          transition={{ duration: 0.3 }}
        />
      </motion.div>

      {/* 错误信息 */}
      {error && (
        <motion.p
          className="mt-2 text-sm text-red-400"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {error}
        </motion.p>
      )}

      {/* 字符计数或帮助文本 */}
      {focused && !error && (
        <motion.div
          className="mt-2 text-xs text-gray-400"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {type === 'password' && '密码应包含至少8个字符'}
          {type === 'email' && '请输入有效的邮箱地址'}
        </motion.div>
      )}
    </div>
  );
};

export default Input;