import React, {useMemo, useState} from 'react'
import PropTypes from 'prop-types'

/*
Mock shape:
interface FinanceRecord {
  period: string // YYYY-MM
  revenue: number
  cogs: number
  cash_balance: number
  avg_daily_net_burn: number
}

Example mock (includes edge-case negative revenue):
const MOCK_FINANCE = [
  {period:'2025-11', revenue: 50000, cogs: 20000, cash_balance: 120000, avg_daily_net_burn: 2000},
  {period:'2025-10', revenue: 45000, cogs: 22000, cash_balance: 0, avg_daily_net_burn: 2500},
  {period:'2025-09', revenue: 0, cogs: 0, cash_balance: 50000, avg_daily_net_burn: 0} // edge: zero burn
]

// TODO: replace with fetch('/api/finance/summary?period=2025-11')
// Sample response: [{"period":"2025-11","revenue":50000,"cogs":20000,"cash_balance":120000,"avg_daily_net_burn":2000}, ...]
// Caching: financial numbers 15m; cash runway real-time via websocket or short-poll

function safeNumber(n){ return (n === null || n === undefined || Number.isNaN(Number(n))) ? 0 : Number(n) }

function grossMarginPercent(revenue, cogs){
  revenue = safeNumber(revenue)
  cogs = safeNumber(cogs)
  if (revenue === 0) return 0
  return ((revenue - cogs)/revenue)*100
}

function cashRunwayDays(cash, avgDailyBurn){
  const burn = safeNumber(avgDailyBurn)
  if (burn <= 0) return Infinity
  return safeNumber(cash)/burn
}

const ManagerFinanceDashboard = ({data = MOCK_FINANCE}) => {
  const [fin] = useState(data)
  const current = fin[0] || {}
  const gm = useMemo(()=>grossMarginPercent(current.revenue, current.cogs), [current])
  const runway = useMemo(()=>cashRunwayDays(current.cash_balance, current.avg_daily_net_burn), [current])

  const approveClose = () => {
    const payload = { month: current.period || 'YYYY-MM', approved_by: 'eve' }
    console.log('POST /api/finance/close', payload)
    // TODO: axios.post('/api/finance/close', payload) and optimistically mark closed
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Manager Finance Dashboard</h2>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-white shadow rounded p-3">
          <div className="text-sm text-gray-500">Gross Margin (%)</div>
          <div className="text-2xl font-bold">{gm.toFixed(1)}%</div>
        </div>
        <div className="bg-white shadow rounded p-3">
          <div className="text-sm text-gray-500">Cash Runway (days)</div>
          <div className="text-2xl font-bold">{runway===Infinity? '∞' : runway.toFixed(0)}</div>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-medium">Financial Summary</h3>
        <div className="mt-2 text-sm">
          <div>Revenue: ${safeNumber(current.revenue).toLocaleString()}</div>
          <div>COGS: ${safeNumber(current.cogs).toLocaleString()}</div>
          <div>Cash: ${safeNumber(current.cash_balance).toLocaleString()}</div>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-medium">Quick Actions</h3>
        <p className="text-sm text-gray-500">Approve monthly close (simulated)</p>
        <button onClick={approveClose} className="mt-2 px-3 py-1 bg-rose-600 text-white rounded">Approve monthly close</button>
      </div>
    </div>
  )
}

ManagerFinanceDashboard.propTypes = { data: PropTypes.array }

export default ManagerFinanceDashboard
