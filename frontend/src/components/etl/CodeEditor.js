import React from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { sql } from '@codemirror/lang-sql';
import { oneDark } from '@codemirror/theme-one-dark';

/**
 * 专业的代码编辑器组件，支持语法高亮
 * 基于CodeMirror实现
 */
const CodeEditor = ({ value, onChange, language = 'sql', theme = 'light', height = '300px' }) => {
  // 处理编辑器内容变化
  const handleChange = (value) => {
    if (onChange) {
      onChange(value);
    }
  };

  // 根据传入的语言参数选择语言扩展
  const getLanguageExtension = () => {
    switch (language.toLowerCase()) {
      case 'sql':
        return sql();
      default:
        return sql(); // 默认使用SQL
    }
  };

  // 根据主题选择相应的样式
  const getThemeExtension = () => {
    switch (theme.toLowerCase()) {
      case 'dark':
        return oneDark;
      default:
        return []; // 默认使用亮色主题
    }
  };

  return (
    <div style={{ border: '1px solid #ddd', borderRadius: '4px', overflow: 'hidden' }}>
      <CodeMirror
        value={value}
        height={height}
        extensions={[getLanguageExtension()]}
        theme={getThemeExtension()}
        onChange={handleChange}
        basicSetup={{
          lineNumbers: true,
          highlightActiveLineGutter: true,
          highlightSpecialChars: true,
          foldGutter: true,
          dropCursor: true,
          allowMultipleSelections: true,
          indentOnInput: true,
          syntaxHighlighting: true,
          bracketMatching: true,
          closeBrackets: true,
          autocompletion: true,
          rectangularSelection: true,
          crosshairCursor: true,
          highlightActiveLine: true,
          highlightSelectionMatches: true,
          closeBracketsKeymap: true,
          searchKeymap: true,
          foldKeymap: true,
          completionKeymap: true,
          lintKeymap: true,
        }}
      />
    </div>
  );
};

export default CodeEditor;