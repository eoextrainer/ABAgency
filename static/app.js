const state = {
  assets: [],
  filters: ["all", "events", "backstage", "classes", "artists"],
  activeFilter: "all",
};

const navToggle = document.querySelector(".nav-toggle");
const navLinks = document.querySelector(".nav-links");
navToggle.addEventListener("click", () => {
  const expanded = navToggle.getAttribute("aria-expanded") === "true";
  navToggle.setAttribute("aria-expanded", String(!expanded));
  navLinks.classList.toggle("open");
});

navLinks.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    navLinks.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
  });
});

const smoothScroll = () => {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (event) => {
      event.preventDefault();
      const target = document.querySelector(anchor.getAttribute("href"));
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
};

const parallaxElements = Array.from(document.querySelectorAll("[data-parallax]"));
const onScroll = () => {
  const offset = window.scrollY;
  parallaxElements.forEach((el) => {
    const speed = Number(el.dataset.parallax || 0.1);
    el.style.transform = `translateY(${offset * speed * 0.2}px)`;
  });
};

const renderHero = (videos) => {
  const heroMedia = document.getElementById("heroMedia");
  if (!heroMedia) {
    console.warn("renderHero skipped: #heroMedia not found");
    return;
  }
  heroMedia.innerHTML = "";
  videos.slice(0, 3).forEach((asset) => {
    const card = document.createElement("div");
    card.className = "video-tile";
    card.innerHTML = `
      <video muted loop playsinline preload="none" data-src="${asset.filepath}"></video>
      <div class="overlay">
        <h4>${asset.title}</h4>
        <span class="play">Lecture immersive</span>
      </div>
    `;
    heroMedia.appendChild(card);
  });
};

const renderCarousel = (containerId, items) => {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  items.forEach((asset) => {
    const item = document.createElement("div");
    item.className = "carousel-item";
    if (asset.asset_type === "video") {
      item.innerHTML = `<video muted loop playsinline preload="none" data-src="${asset.filepath}"></video>`;
    } else {
      item.innerHTML = `<img src="${asset.filepath}" alt="${asset.title}" loading="lazy" />`;
    }
    container.appendChild(item);
  });
};

const renderGalleryFilters = () => {
  console.log("renderGalleryFilters called");
  const filterButtons = document.querySelectorAll(".filter-btn");
  console.log("Found filter buttons:", filterButtons.length);
  
  if (filterButtons.length === 0) {
    console.warn("No filter buttons found!");
    return;
  }
  
  filterButtons.forEach((btn) => {
    const filter = btn.getAttribute("data-filter");
    console.log("Setting up button for filter:", filter);
    btn.classList.toggle("active", filter === state.activeFilter);
    btn.removeEventListener("click", handleFilterClick);
    btn.addEventListener("click", handleFilterClick);
  });
};

const handleFilterClick = (e) => {
  const filter = e.target.getAttribute("data-filter");
  console.log("Filter clicked:", filter);
  state.activeFilter = filter;
  renderGalleryFilters();
  renderMediaGrid();
};

const renderMediaGrid = () => {
  console.log("renderMediaGrid called, activeFilter:", state.activeFilter);
  const grid = document.getElementById("mediaGrid");
  console.log("mediaGrid element found:", !!grid);
  console.log("state.assets length:", state.assets.length);
  
  if (!grid) {
    console.error("mediaGrid element not found!");
    return;
  }
  
  if (!state.assets || state.assets.length === 0) {
    console.error("No assets in state! state.assets:", state.assets);
    grid.innerHTML = '<div class="no-media-message">Aucun média disponible. Vérifiez les logs.</div>';
    return;
  }
  
  grid.innerHTML = "";
  
  const filtered = state.assets.filter((asset) => {
    if (state.activeFilter === "all") return true;
    return asset.category === state.activeFilter;
  });

  console.log(`Filtered ${filtered.length} assets (total: ${state.assets.length}, filter: ${state.activeFilter})`);

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="no-media-message">Aucun média trouvé pour cette catégorie.</div>';
    return;
  }

  filtered.forEach((asset) => {
    const card = document.createElement("div");
    card.className = "media-card";
    card.dataset.type = asset.asset_type;
    card.dataset.src = asset.filepath;
    
    const isVideo = asset.asset_type === "video";
    const playButtonHTML = isVideo ? '<div class="play-button">&#9654;</div>' : '';
    const mediaHTML = isVideo 
      ? `<video muted playsinline preload="metadata" data-src="${asset.filepath}"></video>`
      : `<img src="${asset.filepath}" alt="${asset.title}" loading="lazy" />`;
    
    card.innerHTML = `
      <div class="media-content">
        ${mediaHTML}
        ${playButtonHTML}
        <div class="media-label">
          <div class="media-title">${asset.title}</div>
          <div class="media-category">${asset.category}</div>
        </div>
      </div>
    `;
    
    card.addEventListener("click", () => openLightbox(asset));
    grid.appendChild(card);
  });
  
  console.log(`✅ Rendered ${filtered.length} media items`);
};

const openLightbox = (asset) => {
  const lightbox = document.getElementById("lightbox");
  const content = document.getElementById("lightboxContent");
  content.innerHTML = asset.asset_type === "video"
    ? `<video src="${asset.filepath}" controls autoplay></video>`
    : `<img src="${asset.filepath}" alt="${asset.title}" />`;
  lightbox.classList.add("active");
};

const closeLightbox = () => {
  document.getElementById("lightbox").classList.remove("active");
  document.getElementById("lightboxContent").innerHTML = "";
};

const setupLightbox = () => {
  document.querySelector(".lightbox-close").addEventListener("click", closeLightbox);
  document.getElementById("lightbox").addEventListener("click", (event) => {
    if (event.target.id === "lightbox") {
      closeLightbox();
    }
  });
};

const renderTimeline = async () => {
  const res = await fetch("/milestones");
  const data = await res.json();
  const track = document.getElementById("timelineTrack");
  track.innerHTML = "";
  data.milestones.forEach((milestone) => {
    const card = document.createElement("div");
    card.className = "timeline-card";
    const assets = state.assets.filter((asset) => milestone.media_assets.includes(asset.id));
    const mediaHtml = assets
      .map((asset) => {
        if (asset.asset_type === "video") {
          return `<div class="image-tile"><video muted loop playsinline preload="none" data-src="${asset.filepath}"></video></div>`;
        }
        return `<div class="image-tile"><img src="${asset.filepath}" alt="${asset.title}" loading="lazy" /></div>`;
      })
      .join("");

    card.innerHTML = `
      <div>
        <h4>${milestone.year}</h4>
        <p>${milestone.title}</p>
      </div>
      <div>
        <p>${milestone.description}</p>
        <button type="button">Voir les medias</button>
        <div class="timeline-media">${mediaHtml}</div>
      </div>
    `;
    card.querySelector("button").addEventListener("click", () => {
      card.classList.toggle("expanded");
    });
    track.appendChild(card);
  });
};

const renderCalendar = async () => {
  const res = await fetch("/booking/availability");
  const data = await res.json();
  const calendar = document.getElementById("bookingCalendar");
  calendar.innerHTML = "";
  data.availability.slice(0, 12).forEach((slot) => {
    const day = document.createElement("div");
    day.className = `day ${slot.status}`;
    day.innerHTML = `<strong>${slot.date}</strong><br /><span>${slot.status}</span>`;
    calendar.appendChild(day);
  });
};

const renderTestimonials = () => {
  const testimonials = [
    {
      name: "Directrice artistique",
      quote: "Une energie remarquable et une precision rare dans les scenes acrobatiques.",
    },
    {
      name: "Responsable evenementiel",
      quote: "Une equipe professionnelle qui a transforme notre lancement en show immersif.",
    },
    {
      name: "Producteur",
      quote: "L'approche narrative et l'attention aux details ont impressionne toute la production.",
    },
  ];
  const container = document.getElementById("testimonials");
  container.innerHTML = "";
  testimonials.forEach((item) => {
    const card = document.createElement("div");
    card.className = "testimonial-card";
    card.innerHTML = `<p>"${item.quote}"</p><strong>${item.name}</strong>`;
    container.appendChild(card);
  });
};

const setupForm = () => {
  const form = document.getElementById("contactForm");
  const status = document.getElementById("formStatus");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "Envoi en cours...";
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    try {
      const res = await fetch("/inquiry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error();
      status.textContent = "Merci, votre message a bien ete envoye.";
      form.reset();
    } catch (error) {
      status.textContent = "Erreur: veuillez reessayer plus tard.";
    }
  });
};

const setupVideoLazyLoading = () => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const video = entry.target;
          if (!video.src) {
            video.src = video.dataset.src;
          }
          video.play().catch(() => {});
        }
      });
    },
    { threshold: 0.4 }
  );

  document.querySelectorAll("video[data-src]").forEach((video) => {
    observer.observe(video);
  });
};

const registerServiceWorker = () => {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  }
};

const bootstrap = async () => {
  console.log("=== BOOTSTRAP START ===");
  try {
    console.log("Step 1: smoothScroll()");
    smoothScroll();
    
    console.log("Step 2: setupLightbox()");
    setupLightbox();
    
    console.log("Step 3: setupForm()");
    setupForm();
    
    console.log("Step 4: addEventListener scroll");
    window.addEventListener("scroll", onScroll, { passive: true });

    console.log("Step 5: fetch /assets");
    const res = await fetch("/assets");
    console.log("Response status:", res.status, "ok:", res.ok);
    
    if (!res.ok) {
      throw new Error(`Failed to fetch assets: ${res.status}`);
    }
    
    const data = await res.json();
    console.log("Parsed response:", data);
    state.assets = data.assets || [];
    console.log(`✅ Loaded ${state.assets.length} assets from server`);

    // Shuffle assets randomly for media section
    state.assets = state.assets.sort(() => Math.random() - 0.5);

    const videos = state.assets.filter((asset) => asset.asset_type === "video");
    const images = state.assets.filter((asset) => asset.asset_type === "image");
    
    console.log(`Videos: ${videos.length}, Images: ${images.length}`);

    console.log("Step 6: renderHero");
    renderHero(videos);
    
    console.log("Step 7: renderAgencyCarousel");
    renderAgencyCarousel(videos);
    
    console.log("Step 8: renderGalleryFilters");
    renderGalleryFilters();
    
    console.log("Step 9: renderMediaGrid");
    renderMediaGrid();
    
    console.log("Step 10: setupVideoLazyLoading");
    setupVideoLazyLoading();
    
    console.log("Step 11: registerServiceWorker");
    registerServiceWorker();
    
    console.log("=== BOOTSTRAP COMPLETED ✅ ===");
  } catch (error) {
    console.error("❌ ERROR DURING BOOTSTRAP:", error);
    console.error("Error message:", error.message);
    console.error("Stack:", error.stack);
  }
};

// Carousel scroll function
function scrollCarousel(carouselId, direction) {
  const carousel = document.getElementById(carouselId);
  const scrollAmount = carousel.offsetWidth * 0.8;
  carousel.scrollBy({
    left: direction * scrollAmount,
    behavior: 'smooth'
  });
}

// Render agency carousel with borderless design
const renderAgencyCarousel = (videos) => {
  const container = document.getElementById("agencyVideoCarousel");
  if (!container) return;
  container.innerHTML = "";
  
  videos.slice(0, 8).forEach((asset) => {
    const item = document.createElement("div");
    item.className = "carousel-item";
    item.innerHTML = `<video muted loop playsinline preload="none" data-src="${asset.filepath}"></video>`;
    container.appendChild(item);
  });
};

// Render 2026 calendar
const render2026Calendar = () => {
  const calendarGrid = document.getElementById("yearCalendar2026");
  console.log("Calendar grid element:", calendarGrid);
  
  if (!calendarGrid) {
    console.error("Calendar grid element not found!");
    return;
  }
  
  const months = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
  ];
  
  const events2026 = {
    "Février": [
      { date: "15 Fév", name: "Spectacle Gala" },
      { date: "28 Fév", name: "Performance Privée" }
    ],
    "Mars": [
      { date: "10 Mar", name: "Festival Printemps" },
      { date: "22 Mar", name: "Événement Corporate" }
    ],
    "Avril": [
      { date: "5 Avr", name: "Showcase Danse" }
    ],
    "Mai": [
      { date: "1 Mai", name: "Gala de Charité" },
      { date: "20 Mai", name: "Show Aérien" }
    ],
    "Juin": [
      { date: "15 Juin", name: "Festival d'Été" }
    ],
    "Septembre": [
      { date: "10 Sep", name: "Rentrée Artistique" }
    ],
    "Octobre": [
      { date: "31 Oct", name: "Soirée Spéciale" }
    ],
    "Décembre": [
      { date: "15 Déc", name: "Gala de Noël" },
      { date: "31 Déc", name: "Réveillon Spectacle" }
    ]
  };
  
  calendarGrid.innerHTML = "";
  
  months.forEach((month) => {
    const tile = document.createElement("div");
    tile.className = "month-tile";
    
    const monthEvents = events2026[month] || [];
    const eventsHTML = monthEvents.length > 0
      ? monthEvents.map(event => `
          <div class="event-item">
            <span class="event-date">${event.date}</span>
            ${event.name}
          </div>
        `).join("")
      : '<p style="color: var(--muted); font-size: 0.85rem;">Aucun événement prévu</p>';
    
    tile.innerHTML = `
      <h3>${month}</h3>
      <div class="month-events">
        ${eventsHTML}
      </div>
    `;
    
    calendarGrid.appendChild(tile);
  });
  
  console.log("Calendar rendered with", months.length, "months");
};

// Calendar Modal Functions
const monthData = {
  janvier: {
    month: "Janvier 2026",
    events: ["Aucun événement prévu"]
  },
  fevrier: {
    month: "Février 2026",
    events: [
      "15 Février - Spectacle Gala",
      "28 Février - Performance Privée"
    ]
  },
  mars: {
    month: "Mars 2026",
    events: [
      "10 Mars - Festival Printemps",
      "22 Mars - Événement Corporate"
    ]
  },
  avril: {
    month: "Avril 2026",
    events: [
      "5 Avril - Showcase Danse"
    ]
  },
  mai: {
    month: "Mai 2026",
    events: [
      "1 Mai - Gala de Charité",
      "20 Mai - Show Aérien"
    ]
  },
  juin: {
    month: "Juin 2026",
    events: [
      "15 Juin - Festival d'Été"
    ]
  },
  juillet: {
    month: "Juillet 2026",
    events: ["Aucun événement prévu"]
  },
  aout: {
    month: "Août 2026",
    events: ["Aucun événement prévu"]
  },
  septembre: {
    month: "Septembre 2026",
    events: [
      "10 Septembre - Rentrée Artistique"
    ]
  },
  octobre: {
    month: "Octobre 2026",
    events: [
      "31 Octobre - Soirée Spéciale"
    ]
  },
  novembre: {
    month: "Novembre 2026",
    events: ["Aucun événement prévu"]
  },
  decembre: {
    month: "Décembre 2026",
    events: [
      "15 Décembre - Gala de Noël",
      "31 Décembre - Réveillon Spectacle"
    ]
  }
};

function openMonthModal(monthName, monthKey) {
  const modal = document.getElementById("monthModal");
  const modalTitle = document.getElementById("modalMonthTitle");
  const eventsList = document.getElementById("modalEventsList");
  
  const data = monthData[monthKey];
  if (!data) return;
  
  modalTitle.textContent = data.month;
  
  if (data.events[0] === "Aucun événement prévu") {
    eventsList.innerHTML = '<p style="color: var(--muted); text-align: center; padding: 20px;">Aucun événement prévu pour ce mois</p>';
  } else {
    eventsList.innerHTML = data.events.map(event => `
      <div class="month-modal-event">
        <div style="display: flex; gap: 10px;">
          <span style="color: var(--accent); font-weight: bold; min-width: 120px;">${event.split(' - ')[0]}</span>
          <span>${event.split(' - ')[1] || event}</span>
        </div>
      </div>
    `).join("");
  }
  
  modal.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeMonthModal(event) {
  // If event.stopPropagation was called, event is undefined
  const modal = document.getElementById("monthModal");
  modal.style.display = "none";
  document.body.style.overflow = "auto";
}

bootstrap();
