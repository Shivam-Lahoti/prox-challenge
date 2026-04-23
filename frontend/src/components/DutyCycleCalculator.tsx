import { useState } from 'react'

interface DutyCycleData {
  duty_cycles: any
  initial_values: {
    process: string
    voltage: string
    amperage: string
  }
}

export default function DutyCycleCalculator({ data }: { data: DutyCycleData }) {
  const [process, setProcess] = useState(data.initial_values.process)
  const [voltage, setVoltage] = useState(data.initial_values.voltage)
  const [amperage, setAmperage] = useState(data.initial_values.amperage)

  const calculate = () => {
    const voltageKey = `${voltage}V`
    const amperageKey = `${amperage}A`
    
    const result = data.duty_cycles[process]?.[voltageKey]?.[amperageKey]
    
    if (!result) return null

    const dutyCycle = result.duty_cycle
    const weldMinutes = ((dutyCycle / 100) * 10).toFixed(1)
    const restMinutes = (10 - parseFloat(weldMinutes)).toFixed(1)

    return {
      dutyCycle,
      weldMinutes,
      restMinutes,
      continuous: result.continuous
    }
  }

  const result = calculate()

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-slate-200 max-w-2xl">
      <h3 className="text-xl font-bold text-slate-800 mb-4">
        ⚡ Duty Cycle Calculator
      </h3>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Process
          </label>
          <select
            value={process}
            onChange={(e) => setProcess(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-orange-500"
          >
            <option value="MIG">MIG</option>
            <option value="TIG">TIG</option>
            <option value="Stick">Stick</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Voltage
          </label>
          <select
            value={voltage}
            onChange={(e) => setVoltage(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-orange-500"
          >
            <option value="120">120V</option>
            <option value="240">240V</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Amperage
          </label>
          <input
            type="number"
            value={amperage}
            onChange={(e) => setAmperage(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-orange-500"
          />
        </div>
      </div>

      {result ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-orange-50 p-4 rounded-lg text-center">
              <div className="text-3xl font-bold text-orange-600">
                {result.dutyCycle}%
              </div>
              <div className="text-sm text-slate-600 mt-1">Duty Cycle</div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <div className="text-3xl font-bold text-blue-600">
                {result.continuous}A
              </div>
              <div className="text-sm text-slate-600 mt-1">Continuous Use</div>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-4">
            <h4 className="font-semibold text-slate-800 mb-2">
              Per 10-Minute Period:
            </h4>
            <div className="flex justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                <span>Weld: <strong>{result.weldMinutes} min</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                <span>Rest: <strong>{result.restMinutes} min</strong></span>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
            <p className="text-xs text-yellow-800">
              ⚠️ <strong>Important:</strong> Exceeding duty cycle can overheat and damage the welder.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-center">
          <p className="text-yellow-800">
            No duty cycle data for this combination. Check the manual.
          </p>
        </div>
      )}
    </div>
  )
}