/* ==========================================
   Dataset Index
========================================== */

/*
 * This is a temporary dataset index.
 *
 * The dataset list will later be generated automatically
 * from dataset metadata so that metadata.yaml remains
 * the authoritative source.
 */

const datasets = [
  {
    domain: "School Codes / Japan",
    title: "MEXT School Codes",
    description:
      "文部科学省が公開する学校コードを、再利用しやすい形式へ整理したデータセットです。",
    path: "./school-codes-jp/mext-school-codes/"
  }
];


/* ==========================================
   Dataset Rendering
========================================== */

function renderDatasetList() {
  const datasetList = document.querySelector("#dataset-list");
  const datasetCount = document.querySelector("#dataset-count");

  if (!datasetList || !datasetCount) {
    return;
  }

  datasetList.replaceChildren();

  for (const dataset of datasets) {
    const link = document.createElement("a");

    link.className = "dataset-card";
    link.href = dataset.path;

    const label = document.createElement("p");
    label.className = "dataset-card-label";
    label.textContent = dataset.domain;

    const title = document.createElement("h3");
    title.textContent = dataset.title;

    const description = document.createElement("p");
    description.textContent = dataset.description;

    link.append(label, title, description);

    datasetList.append(link);
  }

  datasetCount.textContent = `${datasets.length} dataset`;
}


/* ==========================================
   Initialization
========================================== */

renderDatasetList();
