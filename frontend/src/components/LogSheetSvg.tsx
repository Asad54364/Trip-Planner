import type { LogSheet } from '../api/client'
import { hourToX, statusToRow, formatHours } from '../lib/hourToX'

interface Props {
  sheet: LogSheet
  driverInfo: {
    driver_name: string
    driver_id: string
    carrier_name: string
    main_office_address: string
    truck_number: string
    trailer_number: string
  }
}

/* ─── Layout constants ─── */
const W = 960
const HEADER_H = 130
const GRID_TOP = HEADER_H + 10
const GRID_LEFT = 130
const GRID_RIGHT = W - 60
const GRID_W = GRID_RIGHT - GRID_LEFT
const ROW_H = 32
const GRID_ROWS = 4
const GRID_H = ROW_H * GRID_ROWS
const TOTALS_COL_W = 50
const REMARKS_TOP = GRID_TOP + GRID_H + 6
const REMARKS_H = 90
const RECAP_TOP = REMARKS_TOP + REMARKS_H + 10
const RECAP_H = 70
const TOTAL_H = RECAP_TOP + RECAP_H + 10

const ROW_LABELS = ['1. Off Duty', '2. Sleeper Berth', '3. Driving', '4. On Duty\n(Not Driving)']
const STATUS_COLORS: Record<string, string> = {
  OFF_DUTY: '#64748b',
  SLEEPER_BERTH: '#8b5cf6',
  DRIVING: '#22c55e',
  ON_DUTY_NOT_DRIVING: '#f59e0b',
}

const HOUR_LABELS = [
  'Mid-\nnight', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
  'Noon', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11',
  'Mid-\nnight',
]

export default function LogSheetSvg({ sheet, driverInfo }: Props) {
  const hx = (h: number) => hourToX(h, GRID_LEFT, GRID_W - TOTALS_COL_W)
  const rowY = (row: number) => GRID_TOP + row * ROW_H

  return (
    <svg
      viewBox={`0 0 ${W} ${TOTAL_H}`}
      xmlns="http://www.w3.org/2000/svg"
      style={{ width: '100%', height: 'auto', background: 'white' }}
      fontFamily="'Inter', 'Courier New', monospace"
    >
      {/* ─── Header ─── */}
      <text x={20} y={28} fontSize={18} fontWeight={700} fill="#0f172a">
        Driver's Daily Log
      </text>
      <text x={20} y={44} fontSize={9} fill="#64748b">(24 hours)</text>

      {/* Date */}
      <text x={200} y={28} fontSize={11} fill="#334155">
        Date: <tspan fontWeight={600}>{sheet.date}</tspan>
      </text>

      {/* Miles */}
      <text x={380} y={28} fontSize={11} fill="#334155">
        Total Miles Driving Today: <tspan fontWeight={600}>{sheet.total_miles_today}</tspan>
      </text>

      {/* Driver info */}
      <text x={20} y={64} fontSize={10} fill="#334155">
        Driver: <tspan fontWeight={600}>{driverInfo.driver_name}</tspan>
        <tspan dx={20}>ID: </tspan><tspan fontWeight={600}>{driverInfo.driver_id}</tspan>
      </text>
      <text x={20} y={80} fontSize={10} fill="#334155">
        Carrier: <tspan fontWeight={600}>{driverInfo.carrier_name}</tspan>
      </text>
      <text x={20} y={96} fontSize={10} fill="#334155">
        Main Office: <tspan fontWeight={600}>{driverInfo.main_office_address}</tspan>
      </text>
      <text x={20} y={112} fontSize={10} fill="#334155">
        Truck/Tractor: <tspan fontWeight={600}>{driverInfo.truck_number}</tspan>
        <tspan dx={20}>Trailer: </tspan><tspan fontWeight={600}>{driverInfo.trailer_number}</tspan>
      </text>

      {/* Signature line */}
      <line x1={500} y1={75} x2={W - 20} y2={75} stroke="#94a3b8" strokeWidth={0.5} />
      <text x={500} y={88} fontSize={8} fill="#94a3b8">
        I certify these entries are true and correct — Signature
      </text>

      {/* ─── Grid Background ─── */}
      <rect x={GRID_LEFT} y={GRID_TOP} width={GRID_W} height={GRID_H}
        fill="#f8fafc" stroke="#334155" strokeWidth={1} />

      {/* Row labels */}
      {ROW_LABELS.map((label, i) => {
        const lines = label.split('\n')
        return (
          <g key={i}>
            {lines.map((line, li) => (
              <text key={li} x={GRID_LEFT - 6} y={rowY(i) + ROW_H / 2 + (li - (lines.length - 1) / 2) * 10 + 3}
                fontSize={9} fill="#334155" textAnchor="end" fontWeight={500}>
                {line}
              </text>
            ))}
            {/* Row separator */}
            {i > 0 && (
              <line x1={GRID_LEFT} y1={rowY(i)} x2={GRID_LEFT + GRID_W}
                y2={rowY(i)} stroke="#cbd5e1" strokeWidth={0.5} />
            )}
          </g>
        )
      })}

      {/* Hour columns + tick marks */}
      {Array.from({ length: 25 }, (_, h) => {
        const x = hx(h)
        return (
          <g key={h}>
            {/* Vertical hour line */}
            <line x1={x} y1={GRID_TOP} x2={x} y2={GRID_TOP + GRID_H}
              stroke={h === 0 || h === 12 || h === 24 ? '#334155' : '#cbd5e1'}
              strokeWidth={h === 0 || h === 12 || h === 24 ? 1 : 0.5} />
            {/* Hour label */}
            {h < 25 && (
              <>
                {HOUR_LABELS[h].includes('\n') ? (
                  HOUR_LABELS[h].split('\n').map((line, li) => (
                    <text key={li} x={x + (h < 24 ? (hx(1) - hx(0)) / 2 : 0)} y={GRID_TOP - 10 + li * 9}
                      fontSize={7} fill="#64748b" textAnchor="middle">
                      {line}
                    </text>
                  ))
                ) : (
                  h < 24 && (
                    <text x={x + (hx(1) - hx(0)) / 2} y={GRID_TOP - 5}
                      fontSize={8} fill="#64748b" textAnchor="middle">
                      {HOUR_LABELS[h]}
                    </text>
                  )
                )}
              </>
            )}
            {/* 15-min tick marks */}
            {h < 24 && [1, 2, 3].map((q) => {
              const tx = hx(h + q / 4)
              return (
                <line key={q} x1={tx} y1={GRID_TOP}
                  x2={tx} y2={GRID_TOP + GRID_H}
                  stroke="#e2e8f0" strokeWidth={0.3} />
              )
            })}
          </g>
        )
      })}

      {/* Totals column header */}
      <text x={GRID_RIGHT - TOTALS_COL_W / 2} y={GRID_TOP - 5}
        fontSize={8} fill="#334155" textAnchor="middle" fontWeight={600}>
        Total Hours
      </text>
      <line x1={GRID_RIGHT - TOTALS_COL_W} y1={GRID_TOP}
        x2={GRID_RIGHT - TOTALS_COL_W} y2={GRID_TOP + GRID_H}
        stroke="#334155" strokeWidth={1} />

      {/* Totals values */}
      {[
        sheet.totals.off_duty,
        sheet.totals.sleeper_berth,
        sheet.totals.driving,
        sheet.totals.on_duty_not_driving,
      ].map((val, i) => (
        <text key={i} x={GRID_RIGHT - TOTALS_COL_W / 2} y={rowY(i) + ROW_H / 2 + 4}
          fontSize={11} fill="#0f172a" textAnchor="middle" fontWeight={600}>
          {formatHours(val)}
        </text>
      ))}

      {/* ─── Duty Status Lines + Vertical Connectors ─── */}
      {sheet.segments.map((seg, i) => {
        const row = statusToRow(seg.status)
        const y = rowY(row) + ROW_H / 2
        const x1 = hx(seg.start)
        const x2 = hx(seg.end)
        const color = STATUS_COLORS[seg.status] || '#334155'

        return (
          <g key={i}>
            {/* Horizontal duty line */}
            <line x1={x1} y1={y} x2={x2} y2={y}
              stroke={color} strokeWidth={2.5} strokeLinecap="round" />

            {/* Vertical connector to next segment */}
            {i < sheet.segments.length - 1 && (() => {
              const nextRow = statusToRow(sheet.segments[i + 1].status)
              if (nextRow !== row) {
                const cy1 = rowY(Math.min(row, nextRow)) + ROW_H / 2
                const cy2 = rowY(Math.max(row, nextRow)) + ROW_H / 2
                const cx = hx(seg.end)
                return (
                  <line x1={cx} y1={cy1} x2={cx} y2={cy2}
                    stroke="#334155" strokeWidth={1.5} />
                )
              }
              return null
            })()}
          </g>
        )
      })}

      {/* ─── Remarks Row ─── */}
      <rect x={GRID_LEFT} y={REMARKS_TOP} width={GRID_W - TOTALS_COL_W} height={REMARKS_H}
        fill="#fefce8" stroke="#334155" strokeWidth={0.5} rx={2} />
      <text x={GRID_LEFT - 6} y={REMARKS_TOP + 14} fontSize={10} fill="#334155"
        textAnchor="end" fontWeight={600}>
        Remarks
      </text>

      {/* Brackets + labels for stationary segments */}
      {sheet.segments
        .filter((seg) => seg.stationary && (seg.end - seg.start) > 0.05)
        .map((seg, i) => {
          const bx1 = hx(seg.start)
          const bx2 = hx(seg.end)
          const by = REMARKS_TOP + 12
          const tickH = 6
          const label = seg.activity
            ? `${seg.location} — ${seg.activity}`
            : seg.location

          return (
            <g key={`bracket-${i}`}>
              {/* Bracket: ⌐...¬ */}
              <line x1={bx1} y1={by} x2={bx1} y2={by + tickH} stroke="#92400e" strokeWidth={1} />
              <line x1={bx1} y1={by + tickH} x2={bx2} y2={by + tickH} stroke="#92400e" strokeWidth={1} />
              <line x1={bx2} y1={by} x2={bx2} y2={by + tickH} stroke="#92400e" strokeWidth={1} />

              {/* 45° angled label */}
              {label && (bx2 - bx1) > 3 && (
                <text
                  x={(bx1 + bx2) / 2}
                  y={by + tickH + 8}
                  fontSize={7}
                  fill="#78350f"
                  textAnchor="start"
                  transform={`rotate(35 ${(bx1 + bx2) / 2} ${by + tickH + 8})`}
                >
                  {label.length > 40 ? label.slice(0, 38) + '…' : label}
                </text>
              )}
            </g>
          )
        })}

      {/* ─── Recap Box ─── */}
      <rect x={20} y={RECAP_TOP} width={W - 40} height={RECAP_H}
        fill="#f1f5f9" stroke="#334155" strokeWidth={0.5} rx={4} />
      <text x={30} y={RECAP_TOP + 18} fontSize={11} fontWeight={700} fill="#0f172a">
        Recap
      </text>
      <text x={30} y={RECAP_TOP + 36} fontSize={10} fill="#334155">
        On-Duty Hours Today:{' '}
        <tspan fontWeight={600}>
          {formatHours(sheet.totals.combined_driving_and_on_duty)}
        </tspan>
      </text>
      <text x={300} y={RECAP_TOP + 36} fontSize={10} fill="#334155">
        70-hr/8-day Total On Duty:{' '}
        <tspan fontWeight={600}>
          {formatHours(sheet.recap.cycle_hours_used_today)}
        </tspan>
      </text>
      <text x={600} y={RECAP_TOP + 36} fontSize={10} fill="#334155">
        Hours Available Tomorrow:{' '}
        <tspan fontWeight={600} fill="#16a34a">
          {formatHours(Math.max(0, 70 - sheet.recap.cycle_hours_used_today))}
        </tspan>
      </text>
      <text x={30} y={RECAP_TOP + 54} fontSize={9} fill="#64748b">
        Driving: {formatHours(sheet.totals.driving)} | On-Duty Not Driving: {formatHours(sheet.totals.on_duty_not_driving)} | Off Duty: {formatHours(sheet.totals.off_duty)} | Sleeper: {formatHours(sheet.totals.sleeper_berth)}
      </text>
    </svg>
  )
}
