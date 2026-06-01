const bmiCalculatorForm = document.getElementById("bmiCalculatorForm");
const weightInput = document.getElementById("weightInput");
const heightInput = document.getElementById("heightInput");
const bmiValue = document.getElementById("bmiValue");
const bmiCategory = document.getElementById("bmiCategory");
const bmiNote = document.getElementById("bmiNote");
const bmiStatus = document.getElementById("bmiStatus");
const bmiBadge = document.getElementById("bmiBadge");

function roundToTwo(value) {
  return Math.round(value * 100) / 100;
}

function getCategory(bmi) {
  if (bmi < 18.5) {
    return { label: "Underweight", note: "A BMI below 18.5 falls in the underweight range." };
  }

  if (bmi < 25) {
    return { label: "Normal weight", note: "A BMI between 18.5 and 24.9 is considered normal weight." };
  }

  if (bmi < 30) {
    return { label: "Overweight", note: "A BMI between 25 and 29.9 falls in the overweight range." };
  }

  return { label: "Obese", note: "A BMI of 30 or above falls in the obese range." };
}

function showError(message) {
  bmiValue.textContent = "--";
  bmiCategory.textContent = "Check your inputs";
  bmiNote.textContent = message;
  bmiBadge.textContent = "Input needed";
  bmiStatus.textContent = message;
}

bmiCalculatorForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const weight = Number.parseFloat(weightInput.value);
  const height = Number.parseFloat(heightInput.value);

  if (!Number.isFinite(weight) || !Number.isFinite(height)) {
    showError("Please enter both weight and height as numbers.");
    return;
  }

  if (weight <= 0 || height <= 0) {
    showError("Weight and height must be greater than zero.");
    return;
  }

  if (weight > 500 || height > 3) {
    showError("Please enter realistic weight and height values.");
    return;
  }

  const bmi = weight / (height * height);
  const roundedBmi = roundToTwo(bmi);
  const category = getCategory(bmi);

  bmiValue.textContent = roundedBmi.toFixed(2);
  bmiCategory.textContent = category.label;
  bmiNote.textContent = category.note;
  bmiBadge.textContent = category.label;
  bmiStatus.textContent = `BMI calculated successfully for ${weight.toFixed(1)} kg and ${height.toFixed(2)} m.`;
});

bmiValue.textContent = "--";
bmiCategory.textContent = "Your category will appear here.";
bmiNote.textContent = "Enter values in kilograms and meters to begin.";
