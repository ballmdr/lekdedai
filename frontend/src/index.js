import ReactDOM from "react-dom/client"
import LotteryCalculator from "./components/LotteryCalculator"
import LotteryStats from "./components/LotteryStats"
import FormulaDetail from "./components/FormulaDetail"

// Mount Calculator Component
const calculatorElement = document.getElementById("lottery-calculator")
if (calculatorElement) {
  const root = ReactDOM.createRoot(calculatorElement)
  root.render(<LotteryCalculator />)
}

// Mount Stats Component
const statsElement = document.getElementById("lottery-stats")
if (statsElement) {
  const root = ReactDOM.createRoot(statsElement)
  root.render(<LotteryStats />)
}

// Mount Formula Detail Component
const formulaDetailElement = document.getElementById("formula-detail")
if (formulaDetailElement) {
  const formulaId = formulaDetailElement.dataset.formulaId
  const root = ReactDOM.createRoot(formulaDetailElement)
  root.render(<FormulaDetail formulaId={formulaId} />)
}
