const TIME_ZONE = "Europe/Paris";

function getToday() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  }).formatToParts(new Date());

  const values = {};
  parts.forEach((part) => {
    values[part.type] = part.value;
  });

  return `${values.year}-${values.month}-${values.day}`;
}

function formatToday() {
  return new Intl.DateTimeFormat("fr-FR", {
    timeZone: TIME_ZONE,
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric"
  }).format(new Date());
}

function formatUpdatedAt(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    timeZone: TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

async function loadGuests() {
  const dateElement = document.getElementById("date");
  const guestsElement = document.getElementById("guests");
  const footerElement = document.getElementById("footer");
  const updatedElement = document.getElementById("updated");

  dateElement.textContent = formatToday();

  try {
    const response = await fetch(`quotidien.json?v=${Date.now()}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error("Impossible de charger les données.");
    }

    const data = await response.json();

    // Ne jamais afficher des données qui ne correspondent pas à aujourd'hui.
    if (data.date !== getToday()) {
      showNotPublished(guestsElement);
      return;
    }

    if (!Array.isArray(data.guests) || data.guests.length === 0) {
      showNotPublished(guestsElement);
      return;
    }

    data.guests.forEach((guest) => {
      const paragraph = document.createElement("p");
      paragraph.className = "guest";
      paragraph.textContent = guest;
      guestsElement.appendChild(paragraph);
    });

    const updated = formatUpdatedAt(data.updated_at);
    if (updated) {
      updatedElement.textContent = `Mis à jour à ${updated}`;
      footerElement.hidden = false;
    }
  } catch (error) {
    // En cas d'indisponibilité des données, on ne montre jamais les invités d'un autre jour.
    showNotPublished(guestsElement);
  }
}

function showNotPublished(container) {
  const message = document.createElement("p");
  message.className = "guest";
  message.textContent = "Liste des invités non publiée";
  container.appendChild(message);
}

loadGuests();
