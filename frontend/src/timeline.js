/**
 * JARVIS-AML Timeline Controller
 * Manages synchronized stage-by-stage temporal progression across the financial graph.
 */

class TimelineController {
  constructor(sliderId, playBtnId, resetBtnId, labelId, markersId) {
    this.slider = document.getElementById(sliderId);
    this.playBtn = document.getElementById(playBtnId);
    this.resetBtn = document.getElementById(resetBtnId);
    this.label = document.getElementById(labelId);
    this.markersContainer = document.getElementById(markersId);

    this.stages = [];
    this.isPlaying = false;
    this.playInterval = null;
    this.currentStageIndex = 0;

    this.initEvents();
  }

  setStages(stages) {
    this.stages = stages || [];
    this.slider.max = Math.max(this.stages.length - 1, 0);
    this.slider.value = 0;
    this.currentStageIndex = 0;
    this.renderMarkers();
    this.updateStageDisplay();
  }

  renderMarkers() {
    this.markersContainer.innerHTML = "";
    this.stages.forEach((stage, idx) => {
      const span = document.createElement("span");
      span.className = `marker ${idx === this.currentStageIndex ? "active" : ""}`;
      span.textContent = stage.stage_name;
      span.addEventListener("click", () => this.setStage(idx));
      this.markersContainer.appendChild(span);
    });
  }

  initEvents() {
    this.slider.addEventListener("input", e => {
      this.setStage(parseInt(e.target.value, 10));
    });

    this.playBtn.addEventListener("click", () => this.togglePlay());
    this.resetBtn.addEventListener("click", () => this.reset());
  }

  setStage(index) {
    if (!this.stages.length) return;
    this.currentStageIndex = Math.min(Math.max(index, 0), this.stages.length - 1);
    this.slider.value = this.currentStageIndex;
    this.updateStageDisplay();

    if (this.onStageChange) {
      this.onStageChange(this.stages[this.currentStageIndex]);
    }
  }

  updateStageDisplay() {
    const stage = this.stages[this.currentStageIndex];
    if (!stage) {
      this.label.textContent = "TIMELINE READY";
      return;
    }

    this.label.textContent = `STAGE ${this.currentStageIndex + 1}: ${stage.stage_name} (${stage.time_range_display || ""})`;

    // Update marker classes
    const markers = this.markersContainer.querySelectorAll(".marker");
    markers.forEach((m, i) => {
      if (i === this.currentStageIndex) {
        m.classList.add("active");
      } else {
        m.classList.remove("active");
      }
    });
  }

  togglePlay() {
    if (this.isPlaying) {
      this.stop();
    } else {
      this.start();
    }
  }

  start() {
    if (!this.stages.length) return;
    this.isPlaying = true;
    this.playBtn.textContent = "⏸ Pause";
    this.playInterval = setInterval(() => {
      let next = this.currentStageIndex + 1;
      if (next >= this.stages.length) {
        next = 0;
      }
      this.setStage(next);
    }, 2200);
  }

  stop() {
    this.isPlaying = false;
    this.playBtn.textContent = "▶ Play";
    if (this.playInterval) {
      clearInterval(this.playInterval);
      this.playInterval = null;
    }
  }

  reset() {
    this.stop();
    this.setStage(0);
  }
}

window.TimelineController = TimelineController;
