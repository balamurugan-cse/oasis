const passwordOutput = document.getElementById("passwordOutput");
const copyButton = document.getElementById("copyButton");
const generatorForm = document.getElementById("generatorForm");
const lengthInput = document.getElementById("lengthInput");
const lengthValue = document.getElementById("lengthValue");
const lowercaseInput = document.getElementById("lowercaseInput");
const uppercaseInput = document.getElementById("uppercaseInput");
const numbersInput = document.getElementById("numbersInput");
const symbolsInput = document.getElementById("symbolsInput");
const strengthBadge = document.getElementById("strengthBadge");
const generatorStatus = document.getElementById("generatorStatus");

const pools = {
  lowercase: "abcdefghijklmnopqrstuvwxyz",
  uppercase: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  numbers: "0123456789",
  symbols: "!@#$%^&*()-_=+[]{};:,.?/",
};

function randomInt(max) {
  return crypto.getRandomValues(new Uint32Array(1))[0] % max;
}

function pickCharacter(source) {
  return source[randomInt(source.length)];
}

function shuffleCharacters(values) {
  for (let index = values.length - 1; index > 0; index -= 1) {
    const swapIndex = randomInt(index + 1);
    [values[index], values[swapIndex]] = [values[swapIndex], values[index]];
  }
  return values;
}

function getSelectedPools() {
  const selected = [];
  if (lowercaseInput.checked) selected.push(pools.lowercase);
  if (uppercaseInput.checked) selected.push(pools.uppercase);
  if (numbersInput.checked) selected.push(pools.numbers);
  if (symbolsInput.checked) selected.push(pools.symbols);
  return selected;
}

function scoreStrength(length, poolCount) {
  if (length < 12 || poolCount < 2) return "Weak";
  if (length < 18 || poolCount < 3) return "Good";
  return "Strong";
}

function generatePassword() {
  const length = Number(lengthInput.value);
  const selectedPools = getSelectedPools();

  if (selectedPools.length === 0) {
    generatorStatus.textContent = "Select at least one character set.";
    strengthBadge.textContent = "Needs options";
    passwordOutput.value = "";
    return;
  }

  const characters = [];
  for (const pool of selectedPools) {
    characters.push(pickCharacter(pool));
  }

  const combinedPool = selectedPools.join("");
  while (characters.length < length) {
    characters.push(pickCharacter(combinedPool));
  }

  const password = shuffleCharacters(characters).join("");
  passwordOutput.value = password;
  generatorStatus.textContent = "Password generated successfully.";
  strengthBadge.textContent = scoreStrength(length, selectedPools.length);
}

lengthInput.addEventListener("input", () => {
  lengthValue.textContent = lengthInput.value;
});

generatorForm.addEventListener("submit", (event) => {
  event.preventDefault();
  generatePassword();
});

copyButton.addEventListener("click", async () => {
  if (!passwordOutput.value) {
    generatePassword();
  }

  if (!passwordOutput.value) {
    return;
  }

  await navigator.clipboard.writeText(passwordOutput.value);
  generatorStatus.textContent = "Password copied to clipboard.";
});

generatePassword();
