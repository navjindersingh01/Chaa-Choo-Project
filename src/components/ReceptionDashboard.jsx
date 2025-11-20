import React, {useMemo, useState} from 'react'
import PropTypes from 'prop-types'

/*
Mock data shape:
interface Reservation {
  id: string
  guest_name: string
  arrival_time: string // ISO timestamp when guest arrived
  checkin_time: string | null // ISO timestamp when checked in
  checkin_date: string // YYYY-MM-DD (date of reservation)
}

Example mock (includes edge-case: late timestamp and null checkin_time):
const MOCK_RESERVATIONS = [
  {id:'r1', guest_name:'John Doe', arrival_time:'2025-11-18T09:05:00+00:00', checkin_time:'2025-11-18T09:12:00+00:00', checkin_date:'2025-11-18'},
  {id:'r2', guest_name:'Ana Smith', arrival_time:'2025-11-18T10:20:00+00:00', checkin_time:null, checkin_date:'2025-11-18'}, // edge: not checked in yet
  {id:'r3', guest_name:'Late Comer', arrival_time:'2025-11-17T23:55:00+00:00', checkin_time:'2025-11-18T00:10:00+00:00', checkin_date:'2025-11-18'}
]

// TODO: replace with fetch('/api/reception/reservations?date=YYYY-MM-DD')
// Sample response: [{"id":"r1","guest_name":"John","arrival_time":"2025-11-18T09:05:00Z","checkin_time":"2025-11-18T09:12:00Z","checkin_date":"2025-11-18"}, ...]
// Caching hint: revalidate every 30s for KPI cards, hourly bar 1m. Use SWR key ['reception','reservations',date]

const MOCK_RESERVATIONS = [
  {id:'r1', guest_name:'John Doe', arrival_time:'2025-11-18T09:05:00+00:00', checkin_time:'2025-11-18T09:12:00+00:00', checkin_date:'2025-11-18'},
  {id:'r2', guest_name:'Ana Smith', arrival_time:'2025-11-18T10:20:00+00:00', checkin_time:null, checkin_date:'2025-11-18'},
  {id:'r3', guest_name:'Late Comer', arrival_time:'2025-11-17T23:55:00+00:00', checkin_time:'2025-11-18T00:10:00+00:00', checkin_date:'2025-11-18'}
]

function safeNumber(n){ return (n === null || n === undefined || Number.isNaN(Number(n))) ? 0 : Number(n) }
function validateDateString(s){ try{ return !Number.isNaN(Date.parse(s)) }catch(e){return false} }

// KPI: Today: Check-ins (count where checkin_date == today)
function countTodayCheckins(records, todayStr){
  if (!Array.isArray(records)) return 0
  return records.filter(r => r.checkin_date === todayStr).length
}

// KPI: Average Wait Time (min) = avg(checkin_time - arrival_time) for records with both timestamps
function avgWaitMins(records){
  const diffs = records.map(r=>{
    if (!r.arrival_time || !r.checkin_time) return null
    const a = Date.parse(r.arrival_time)
    const c = Date.parse(r.checkin_time)
    if (Number.isNaN(a) || Number.isNaN(c)) return null
    return (c - a)/60000
  }).filter(x=>x!==null)
  if (diffs.length===0) return 0
  return diffs.reduce((s,v)=>s+v,0)/diffs.length
}

const ReceptionDashboard = ({data = MOCK_RESERVATIONS}) => {
  const [reservations] = useState(data)
  const today = new Date().toISOString().slice(0,10)
  const todayCount = useMemo(()=>countTodayCheckins(reservations, today), [reservations, today])
  const avgWait = useMemo(()=>avgWaitMins(reservations), [reservations])

  // build hourly arrivals bar (counts per hour)
  const hourly = useMemo(()=>{
    const map = {}
    reservations.forEach(r=>{
      if (!validateDateString(r.arrival_time)) return
      const hour = new Date(r.arrival_time).getHours()
      map[hour] = (map[hour] || 0) + 1
    })
    return map
  }, [reservations])

  // Action: Confirm reservation (simulated)
  const confirmReservation = (id) => {
    const payload = { confirmed_by: 'bob', confirmation_time: new Date().toISOString() }
    console.log('POST /api/reservations/'+id+'/confirm', payload)
    // TODO: axios.post(`/api/reservations/${id}/confirm`, payload) and optimistic update
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Reception Dashboard</h2>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-white shadow rounded p-3">
          <div className="text-sm text-gray-500">Today: Check-ins</div>
          <div className="text-2xl font-bold">{todayCount}</div>
        </div>
        <div className="bg-white shadow rounded p-3">
          <div className="text-sm text-gray-500">Average Wait Time (min)</div>
          <div className="text-2xl font-bold">{avgWait.toFixed(1)}</div>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-medium">Hourly Arrivals</h3>
        <div className="mt-2 grid grid-cols-6 gap-2">
          {Array.from({length:6}).map((_,i)=>{
            const hour = (8+i) % 24
            return (<div key={hour} className="text-center text-sm">
              <div className="bg-gray-100 p-2 rounded">{hour}:00</div>
              <div className="mt-1 font-bold">{hourly[hour] || 0}</div>
            </div>)
          })}
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-medium">Reservations (sample)</h3>
        <ul className="mt-2 text-sm">
          {reservations.map(r=> (
            <li key={r.id} className="py-1 flex justify-between">
              <span>{r.guest_name} • {r.checkin_date}</span>
              <span>
                <button onClick={()=>confirmReservation(r.id)} className="px-2 py-1 bg-blue-600 text-white rounded">Confirm</button>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

ReceptionDashboard.propTypes = { data: PropTypes.array }

export default ReceptionDashboard
