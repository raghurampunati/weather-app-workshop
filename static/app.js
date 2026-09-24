const form = document.getElementById("search-form");
const query = document.getElementById("query");
const statusLine = document.getElementById("status");
const result = document.getElementById("result");
const submit = form.querySelector("button");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const term = query.value.trim();
  if (!term) return;

  setStatus("Loading…");
  result.hidden = true;
  submit.disabled = true;

  try {
    const response = await fetch(`/api/weather?q=${encodeURIComponent(term)}`);
    const payload = await response.json();

    if (!response.ok) {
      setStatus(payload.detail || "Something went wrong.", true);
      return;
    }

    render(payload);
    setStatus("");
  } catch {
    setStatus("Could not reach the server.", true);
  } finally {
    submit.disabled = false;
  }
});

function render({ city, current }) {
  document.getElementById("city").textContent = city.label;
  document.getElementById("icon").textContent = current.icon;
  document.getElementById("temp").textContent =
    `${Math.round(current.temperature)}${current.temperature_unit}`;
  document.getElementById("description").textContent = current.description;
  document.getElementById("feels").textContent =
    `${Math.round(current.apparent_temperature)}${current.temperature_unit}`;
  document.getElementById("humidity").textContent = `${current.humidity}%`;
  document.getElementById("wind").textContent =
    `${current.wind_speed} ${current.wind_speed_unit}`;
  document.getElementById("precip").textContent =
    `${current.precipitation} ${current.precipitation_unit}`;

  const observed = document.getElementById("observed");
  observed.dateTime = current.time;
  observed.textContent = new Date(current.time).toLocaleString();

  result.hidden = false;
}

function setStatus(message, isError = false) {
  statusLine.textContent = message;
  statusLine.classList.toggle("error", isError);
}
