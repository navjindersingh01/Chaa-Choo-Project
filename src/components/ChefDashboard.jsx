import React, {useMemo, useState} from 'react'
import PropTypes from 'prop-types'

/*
Mock data shape (Type-like):
interface WasteRecord {
  id: string
  kitchen_area: string
  weight_kg: number | null // edge-case: null when weight not recorded
  recorded_at: string // ISO timestamp
}

Example mock array (max 10 records):
const MOCK_WASTE = [
  {id: 'w1', kitchen_area: 'Grill', weight_kg: 4.2, recorded_at: '2025-11-17T08:15:00+00:00'},
  {id: 'w2', kitchen_area: 'Prep', weight_kg: 1.0, recorded_at: '2025-11-17T12:30:00+00:00'},
  {id: 'w3', kitchen_area: 'Salad', weight_kg: null, recorded_at: '2025-11-17T18:45:00+00:00'} // edge: null weight -> handle as 0 and surface to ops
]

// TODO: replace with fetch('/api/chef/waste?limit=10')
// Expected JSON sample (max 5 items): [{"id":"w1","kitchen_area":"Grill","weight_kg":4.2,"recorded_at":"2025-11-17T08:15:00Z"}, ...]
// Hint: Use SWR or react-query with key '/api/chef/waste' and revalidate-interval: 60000
// Example axios snippet:
// const {data} = await axios.get('/api/chef/waste?limit=10')
// cacheKey: ['chef','waste']  // revalidate every 60s for KPIs, 5m for charts

const MOCK_WASTE = [
  {id: 'w1', kitchen_area: 'Grill', weight_kg: 4.2, recorded_at: '2025-11-17T08:15:00+00:00'},
  {id: 'w2', kitchen_area: 'Prep', weight_kg: 1.0, recorded_at: '2025-11-17T12:30:00+00:00'},
  {id: 'w3', kitchen_area: 'Salad', weight_kg: null, recorded_at: '2025-11-17T18:45:00+00:00'},
  {id: 'w4', kitchen_area: 'Fryer', weight_kg: 2.5, recorded_at: '2025-11-16T19:10:00+00:00'},
  {id: 'w5', kitchen_area: 'Cold', weight_kg: 0.3, recorded_at: '2025-11-16T06:05:00+00:00'}
]

// small helpers used across KPIs
function safeNumber(n){
  if (n === null || n === undefined || Number.isNaN(Number(n))) return 0
  return Number(n)
}

function validateDateString(s){
  try{ return !Number.isNaN(Date.parse(s)) }catch(e){return false}
}

// KPI calc: daily_waste_kg = sum(waste_items.weight_kg)
export function calcDailyWasteKg(records){
  if (!Array.isArray(records)) return 0
  return records.reduce((acc, r) => acc + safeNumber(r.weight_kg), 0)
}

const Sparkline = ({values=[]}) => {
  // very small inline sparkline using SVG
  const w = 120, h = 30, pad = 2
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const points = values.map((v,i)=>{
    const x = pad + (i/(Math.max(values.length-1,1))) * (w-2*pad)
    const y = h - pad - ((v - min)/(max - min || 1))*(h-2*pad)
    return `${x},${y}`
  }).join(' ')
  return (<svg width={w} height={h} className="inline-block"><polyline fill="none" stroke="#2563eb" strokeWidth="2" points={points} /></svg>)
}

const ChefDashboard = ({data = MOCK_WASTE}) => {
  const [waste] = useState(data)
  const dailyWaste = useMemo(()=>calcDailyWasteKg(waste), [waste])
  const sparkValues = useMemo(()=> waste.slice(-10).map(rec=> safeNumber(rec.weight_kg)), [waste])

  // Actionable: Mark order prepared (this UI lives here as a suggested action)
  const markOrderPrepared = (orderId) => {
    const payload = { status: 'prepared', prepared_by: 'alice', timestamp: new Date().toISOString() }
    // Optimistic UI: update local state before network return (not implemented here)
    console.log('PATCH /api/orders/'+orderId+'/status', payload)
    // TODO: replace console.log with axios.patch(`/api/orders/${orderId}/status`, payload)
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Chef Dashboard</h2>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-white shadow rounded p-3">
          <div className="text-sm text-gray-500">Food Waste (kg/day)</div>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{dailyWaste.toFixed(1)}</div>
            <div className="ml-2"><Sparkline values={sparkValues} /></div>
          </div>
        </div>
        <div className="bg-white shadow rounded p-3">
          <div className="text-sm text-gray-500">Recent Waste Entries</div>
          <ul className="mt-2 text-sm">
            {waste.slice(0,5).map(r=> (
              <li key={r.id} className="py-1 flex justify-between">
                <span>{r.kitchen_area} {validateDateString(r.recorded_at) ? `• ${new Date(r.recorded_at).toLocaleString()}` : ''}</span>
                <span className="font-medium">{safeNumber(r.weight_kg).toFixed(1)} kg</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-medium">Quick Actions</h3>
        <p className="text-sm text-gray-500">Mark an order prepared (simulated)</p>
        <button onClick={()=>markOrderPrepared('order-123')} className="mt-2 px-3 py-1 bg-green-600 text-white rounded">Mark order prepared</button>
      </div>
    </div>
  )
}

ChefDashboard.propTypes = {
  data: PropTypes.array
}

export default ChefDashboard
