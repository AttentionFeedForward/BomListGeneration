import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useBOM, SimpleBOMItem } from '../../store';
import { useNavigation } from '../../App';
import * as XLSX from 'xlsx';
import { FileText } from 'lucide-react';

type EditableItem = {
  index: number;
  code: string; // 物料编码
  name: string;
  specification: string;
  quantity: number;
  unit: string;
  formula: string; // 计算公式
  usage: string; // 材料用途
  notes?: string;
};

const BOMGeneration: React.FC = () => {
  const bom = useBOM();
  const { navigateTo } = useNavigation();

  const [items, setItems] = useState<EditableItem[]>([]);

  useEffect(() => {
    // 优先使用后端返回的完整版 full_bom
    if (bom.materialBom?.full_bom && bom.materialBom.full_bom.length > 0) {
      const mapped = bom.materialBom.full_bom.map((row, i) => {
        let quantity = Number(row.数量 ?? 0);
        const name = String(row.物料名称 ?? '');
        // 阀门按个数计算，需要取整
        if (name.includes('阀门')) {
          quantity = Math.round(quantity);
        }

        return {
          index: Number(row.项次 ?? i + 1),
          code: String(row.物料编码 ?? `MAT-${(i + 1).toString().padStart(3, '0')}`),
          name: name,
          specification: String(row.规格 ?? ''),
          quantity: quantity,
          unit: String(row.单位 ?? ''),
          formula: String(row.计算公式 ?? ''),
          usage: String(row.材料用途 ?? ''),
          notes: String(row.备注 ?? ''),
        };
      });
      setItems(mapped);
    } else if (bom.materialBom?.materials) {
      // 回退到简化 materials 结构
      const mapped = bom.materialBom.materials.map((m: SimpleBOMItem, i: number) => {
        let quantity = m.quantity;
        const name = m.name;
        // 阀门按个数计算，需要取整
        if (name.includes('阀门')) {
          quantity = Math.round(quantity);
        }
        
        return {
          index: i + 1,
          code: m.material_code ?? `MAT-${(i + 1).toString().padStart(3, '0')}`,
          name: name,
          specification: m.specification,
          quantity: quantity,
          unit: m.unit,
          formula: m.calculation_formula ?? '',
          usage: m.usage ?? `${m.category || ''}`,
          notes: m.notes || '',
        };
      });
      setItems(mapped);
    }
  }, [bom.materialBom]);

  const headers = useMemo(
    () => ['序号', '物料编码', '物料名称', '规格', '数量', '单位', '计算公式', '材料用途', '备注'],
    []
  );

  const updateItem = (idx: number, field: keyof EditableItem, value: string | number) => {
    setItems(prev => prev.map((item, i) => (i === idx ? { ...item, [field]: value } : item)));
  };

  const addRow = () => {
    setItems(prev => [
      ...prev,
      {
        index: prev.length + 1,
        code: '',
        name: '',
        specification: '',
        quantity: 0,
        unit: '',
        formula: '',
        usage: '',
        notes: '',
      },
    ]);
  };

  const deleteRow = (idx: number) => {
    setItems(prev => prev.filter((_, i) => i !== idx).map((item, i) => ({ ...item, index: i + 1 })));
  };

  const exportCSV = () => {
    const rows = items.map(r => [
      r.index,
      r.code,
      r.name,
      r.specification,
      r.quantity,
      r.unit,
      r.formula,
      r.usage,
      r.notes || '',
    ]);
    const csvContent = [headers, ...rows]
      .map(row => row
        .map(cell => {
          const str = String(cell ?? '');
          const escaped = '"' + str.replace(/"/g, '""') + '"';
          return escaped;
        })
        .join(',')
      )
      .join('\n');

    const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const ts = new Date().toISOString().slice(0,19).replace(/[:T]/g, '_');
    a.download = `BOM_${ts}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportExcel = () => {
    // Sheet 1: 当前BOM表
    const aoa = [headers, ...items.map(r => [
      r.index,
      r.code,
      r.name,
      r.specification,
      r.quantity,
      r.unit,
      r.formula,
      r.usage,
      r.notes || '',
    ])];
    const ws = XLSX.utils.aoa_to_sheet(aoa);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'BOM明细');

    // Sheet 2: 合并后的BOM表 (同名称同规格合并，保留计算公式)
    const mergedMap = new Map<string, EditableItem>();

    items.forEach(item => {
      // 使用 名称 + 规格 作为唯一键
      const key = `${item.name}|${item.specification}`;
      
      if (mergedMap.has(key)) {
        const existing = mergedMap.get(key)!;
        // 累加数量
        existing.quantity += item.quantity;
        // 合并计算公式
        if (item.formula) {
          if (existing.formula) {
             // 避免重复连接（可选，但这里直接连接）
             existing.formula += ` + ${item.formula}`;
          } else {
            existing.formula = item.formula;
          }
        }
        
        // 合并材料用途
        const existingUsageParts = existing.usage ? existing.usage.split(',').map(s => s.trim()).filter(Boolean) : [];
        const newUsageParts = item.usage ? item.usage.split(',').map(s => s.trim()).filter(Boolean) : [];
        const combinedUsage = Array.from(new Set([...existingUsageParts, ...newUsageParts])).join(', ');
        existing.usage = combinedUsage;

        // 合并备注
        const existingNotesParts = existing.notes ? existing.notes.split(',').map(s => s.trim()).filter(Boolean) : [];
        const newNotesParts = item.notes ? item.notes.split(',').map(s => s.trim()).filter(Boolean) : [];
        const combinedNotes = Array.from(new Set([...existingNotesParts, ...newNotesParts])).join(', ');
        existing.notes = combinedNotes;

      } else {
        // 创建副本以避免修改原数组
        mergedMap.set(key, { ...item });
      }
    });

    const mergedItems = Array.from(mergedMap.values()).map((item, idx) => ({
      ...item,
      index: idx + 1 // 重新生成序号
    }));

    const aoaMerged = [headers, ...mergedItems.map(r => [
      r.index,
      r.code,
      r.name,
      r.specification,
      r.quantity,
      r.unit,
      r.formula,
      r.usage,
      r.notes || '',
    ])];
    
    const wsMerged = XLSX.utils.aoa_to_sheet(aoaMerged);
    XLSX.utils.book_append_sheet(wb, wsMerged, '合并BOM');

    const ts = new Date().toISOString().slice(0,19).replace(/[:T]/g, '_');
    XLSX.writeFile(wb, `BOM_${ts}.xlsx`);
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-white flex items-center">
            <FileText className="mr-3" /> BOM生成
          </h1>
          <div className="flex gap-2">
            <button
              onClick={() => navigateTo('material-calculation')}
              className="px-3 py-2 rounded-lg bg-gray-700 text-gray-200 hover:bg-gray-600"
            >返回物料计算</button>
            <button
              onClick={addRow}
              className="px-3 py-2 rounded-lg bg-blue-700 text-white hover:bg-blue-600"
            >新增行</button>
            <button
              onClick={exportCSV}
              className="px-3 py-2 rounded-lg bg-green-700 text-white hover:bg-green-600"
            >导出CSV</button>
            <button
              onClick={exportExcel}
              className="px-3 py-2 rounded-lg bg-purple-700 text-white hover:bg-purple-600"
            >导出Excel</button>
          </div>
        </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}>
        <div className="glass-effect rounded-xl p-4 border border-white/20 overflow-auto">
          {items.length === 0 ? (
            <div className="text-gray-300">暂无BOM数据，请先在物料计算页面生成。</div>
          ) : (
            <table className="min-w-full text-sm text-gray-200">
              <thead>
                <tr>
                  {headers.map(h => (
                    <th key={h} className="text-left px-3 py-2 border-b border-white/10">{h}</th>
                  ))}
                  <th className="px-3 py-2 border-b border-white/10">操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row, idx) => (
                  <tr key={idx} className="hover:bg-white/5">
                    <td className="px-3 py-2 border-b border-white/10">{row.index}</td>
                    <td className="px-3 py-2 border-b border-white/10">
                      <input
                        value={row.code}
                        onChange={e => updateItem(idx, 'code', e.target.value)}
                        className="w-full bg-transparent border border-white/10 rounded px-2 py-1"
                      />
                    </td>
                    <td className="px-3 py-2 border-b border-white/10">
                      <input
                        value={row.name}
                        onChange={e => updateItem(idx, 'name', e.target.value)}
                        className="w-full bg-transparent border border-white/10 rounded px-2 py-1"
                      />
                    </td>
                    <td className="px-3 py-2 border-b border-white/10">
                      <input
                        value={row.specification}
                        onChange={e => updateItem(idx, 'specification', e.target.value)}
                        className="w-full bg-transparent border border-white/10 rounded px-2 py-1"
                      />
                    </td>
                    <td className="px-3 py-2 border-b border-white/10 w-32">
                      <input
                        type="number"
                        step="0.01"
                        value={row.quantity}
                        onChange={e => updateItem(idx, 'quantity', parseFloat(e.target.value || '0'))}
                        className="w-full bg-transparent border border-white/10 rounded px-2 py-1"
                      />
                    </td>
                    <td className="px-3 py-2 border-b border-white/10 w-28">
                      <input
                        value={row.unit}
                        onChange={e => updateItem(idx, 'unit', e.target.value)}
                        className="w-full bg-transparent border border-white/10 rounded px-2 py-1"
                      />
                    </td>
                    <td className="px-3 py-2 border-b border-white/10">
                      <input
                        value={row.formula}
                        onChange={e => updateItem(idx, 'formula', e.target.value)}
                        className="w-full bg-transparent border border-white/10 rounded px-2 py-1"
                      />
                    </td>
                    <td className="px-3 py-2 border-b border-white/10">
                      <input
                        value={row.usage}
                        onChange={e => updateItem(idx, 'usage', e.target.value)}
                        className="w-full bg-transparent border border-white/10 rounded px-2 py-1"
                      />
                    </td>
                    <td className="px-3 py-2 border-b border-white/10">
                      <input
                        value={row.notes || ''}
                        onChange={e => updateItem(idx, 'notes', e.target.value)}
                        className="w-full bg-transparent border border-white/10 rounded px-2 py-1"
                      />
                    </td>
                    <td className="px-3 py-2 border-b border-white/10">
                      <button
                        onClick={() => deleteRow(idx)}
                        className="px-2 py-1 rounded bg-red-600 text-white hover:bg-red-500"
                      >删除</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default BOMGeneration;