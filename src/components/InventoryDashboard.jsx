import React, {useMemo, useState} from 'react'
import PropTypes from 'prop-types'

/*
Mock data shape:
interface SKU {
  sku: string
  name: string
  current_qty: number
  avg_daily_usage: number // may be zero
}

Example mock (top-5 with edge-case avg_daily_usage=0):
const MOCK_SKUS = [
  {sku:'SKU-001', name:'Tomatoes', current_qty: 120, avg_daily_usage: 30},
  {sku:'SKU-002', name:'Lettuce', current_qty: 8, avg_daily_usage: 5},
  {sku:'SKU-003', name:'Cheese', current_qty: 2, avg_daily_usage: 1},
  {sku:'SKU-004', name:'Olive Oil', current_qty: 50, avg_daily_usage: 0}, // edge: zero usage -> infinite days
  {sku:'SKU-005', name:'Buns', current_qty: 18, avg_daily_usage: 6}
]

// TODO: replace with fetch('/api/inventory/skus?top=5')
// Sample response: [{"sku":"SKU-001","name":"Tomatoes","current_qty":120,"avg_daily_usage":30}, ...]
// NOTE: websocket integration suggested for real-time reorder alerts.
// Example websocket event: {"type":"reorder_alert","sku":"SKU-003","current_qty":2}

function safeNumber(n){ return (n === null || n === undefined || Number.isNaN(Number(n))) ? 0 : Number(n) }

function daysOfStock(item){
  const usage = safeNumber(item.avg_daily_usage)
  if (usage <= 0) return Infinity
  return safeNumber(item.current_qty)/usage
}

const InventoryDashboard = ({data = MOCK_SKUS}) => {
  const [skus] = useState(data)
  const top5 = useMemo(()=>skus.slice(0,5), [skus])

  const approvePO = (poId) => {
    const payload = { approved_by: 'charlie', expected_delivery_date: new Date(Date.now()+7*24*3600*1000).toISOString().slice(0,10) }
    console.log('POST /api/purchase-orders/'+poId+'/approve', payload)
    // TODO: axios.post(`/api/purchase-orders/${poId}/approve`, payload) and optimistically update PO status
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Inventory Dashboard</h2>
      <p className="text-sm text-gray-500">Top-5 SKUs Days of Stock (table)</p>
      <div className="mt-4 bg-white shadow rounded">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-2 text-left">SKU</th>
              <th className="p-2 text-left">Name</th>
              <th className="p-2 text-right">Qty</th>
              <th className="p-2 text-right">Avg/day</th>
              <th className="p-2 text-right">Days of Stock</th>
            </tr>
          </thead>
          <tbody>
            {top5.map(it=>{
              const dos = daysOfStock(it)
              const low = dos !== Infinity && dos <= 3
              return (
                <tr key={it.sku} className="border-t">
                  <td className="p-2">{it.sku}</td>
                  <td className="p-2">{it.name}</td>
                  <td className="p-2 text-right">{safeNumber(it.current_qty)}</td>
                  <td className="p-2 text-right">{safeNumber(it.avg_daily_usage)}</td>
                  <td className="p-2 text-right">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${low ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                      {dos===Infinity? '∞' : dos.toFixed(1)} days
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-4">
        <h3 className="font-medium">Quick Actions</h3>
        <p className="text-sm text-gray-500">Approve a purchase order (simulated)</p>
        <button onClick={()=>approvePO('po-42')} className="mt-2 px-3 py-1 bg-indigo-600 text-white rounded">Approve PO</button>
      </div>
    </div>
  )
}

InventoryDashboard.propTypes = { data: PropTypes.array }

export default InventoryDashboard
