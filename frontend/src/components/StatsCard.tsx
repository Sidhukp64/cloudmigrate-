import { LucideIcon } from 'lucide-react'

interface StatsCardProps {
  label: string
  value: string | number
  icon: LucideIcon
  trend?: { value: string; positive: boolean }
  color?: 'blue' | 'green' | 'red' | 'yellow'
}

const COLOR_MAP = {
  blue: 'text-blue-400 bg-blue-900/40',
  green: 'text-green-400 bg-green-900/40',
  red: 'text-red-400 bg-red-900/40',
  yellow: 'text-yellow-400 bg-yellow-900/40',
}

export default function StatsCard({ label, value, icon: Icon, trend, color = 'blue' }: StatsCardProps) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`p-2.5 rounded-lg ${COLOR_MAP[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-sm text-gray-400">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
        {trend && (
          <p className={`text-xs mt-1 ${trend.positive ? 'text-green-400' : 'text-red-400'}`}>
            {trend.positive ? '▲' : '▼'} {trend.value}
          </p>
        )}
      </div>
    </div>
  )
}
