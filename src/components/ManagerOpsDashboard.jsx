import React, {useMemo, useState} from 'react'
import PropTypes from 'prop-types'

/*
Mock data shape:
interface StaffRecord {
  id: string
  name: string
  worked_hours: number
  scheduled_hours: number // may be zero
}

Example mock (includes staff with zero scheduled_hours edge case):
const MOCK_STAFF = [
  {id:'s1', name:'Alice', worked_hours: 38, scheduled_hours: 40},
  {id:'s2', name:'Bob', worked_hours: 20, scheduled_hours: 20},
  {id:'s3', name:'Charlie', worked_hours: 0, scheduled_hours: 0} // edge: no scheduled hours
]

// TODO: replace with fetch('/api/ops/staff?range=7d')
// Sample: [{"id":"s1","name":"Alice","worked_hours":38,"scheduled_hours":40}, ...]
// Caching: staff data 1m. Use key ['ops','staff']

function safeNumber(n){ return (n === null || n === undefined || Number.isNaN(Number(n))) ? 0 : Number(n) }

function staffUtilPercent(record){
  const scheduled = safeNumber(record.scheduled_hours)
  if (scheduled === 0) return 0
  return (safeNumber(record.worked_hours)/scheduled)*100
}

const Donut = ({percent=0, size=80}) => {
  const stroke = 10
  const radius = (size - stroke)/2
  const circ = 2*Math.PI*radius
  const dash = Math.min(Math.max(percent,0),100)/100 * circ
  return (
    <svg width={size} height={size} className="inline-block">
      <circle cx={size/2} cy={size/2} r={radius} stroke="#e5e7eb" strokeWidth={stroke} fill="none" />
      <circle cx={size/2} cy={size/2} r={radius} stroke="#f97316" strokeWidth={stroke} fill="none" strokeDasharray={`${dash} ${circ-dash}`} transform={`rotate(-90 ${size/2} ${size/2})`} strokeLinecap="round" />
      <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fontSize="12" fill="#111">{Math.round(percent)}%</text>
    </svg>
  )
}

const ManagerOpsDashboard = ({data = MOCK_STAFF}) => {
  const [staff] = useState(data)
  const avgUtil = useMemo(()=>{
    const vals = staff.map(s=>staffUtilPercent(s))
    if (vals.length===0) return 0
    return vals.reduce((a,b)=>a+b,0)/vals.length
  }, [staff])

  const assignShift = () => {
    const payload = { staff_id: 's2', start: new Date().toISOString(), end: new Date(Date.now()+4*3600*1000).toISOString(), assigned_by: 'diana' }
    console.log('POST /api/shifts', payload)
    // TODO: axios.post('/api/shifts', payload) and optimistically append shift to local schedule
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Manager Ops Dashboard</h2>
      <div className="mt-4 flex items-center gap-6">
        <div className="bg-white shadow rounded p-3 flex items-center">
          <div className="mr-4"><Donut percent={avgUtil} /></div>
          <div>
            <div className="text-sm text-gray-500">Staff Utilization</div>
            <div className="text-2xl font-bold">{avgUtil.toFixed(0)}%</div>
            <div className="text-xs text-gray-500">(worked / scheduled)</div>
          </div>
        </div>
        <div className="bg-white shadow rounded p-3 flex-1">
          <div className="text-sm text-gray-500">Trend (last week)</div>
          <div className="mt-2 text-sm">Trend sparkline placeholder</div>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-medium">Staff List</h3>
        <ul className="mt-2 text-sm">
          {staff.map(s=> (
            <li key={s.id} className="py-1 flex justify-between">
              <span>{s.name}</span>
              <span>{Math.round(staffUtilPercent(s))}%</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6">
        <h3 className="font-medium">Quick Actions</h3>
        <p className="text-sm text-gray-500">Assign a shift (simulated)</p>
        <button onClick={assignShift} className="mt-2 px-3 py-1 bg-yellow-600 text-white rounded">Assign shift</button>
      </div>
    </div>
  )
}

ManagerOpsDashboard.propTypes = { data: PropTypes.array }

export default ManagerOpsDashboard
