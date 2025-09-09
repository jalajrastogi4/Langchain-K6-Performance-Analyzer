import os
import base64
from io import BytesIO
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from src.eda.plots import (
    plot_status_distribution,
    plot_endpoint_latencies,
    plot_endpoint_rps
)

class ReportGenerator:
    def __init__(self, template_dir="src/eda/templates", template_file="report_template.html"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template(template_file)

    def fig_to_base64(self, fig):
        """
        Convert matplotlib figure to base64 string for embedding in HTML.
        """
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()
        return f"data:image/png;base64,{img_base64}"

    def generate_report(self, global_metrics, endpoint_metrics, plots, output_file="report.html"):
        """
        Generate an HTML report.
        """
        # Convert figures into base64-encoded images
        plot_images = {name: self.fig_to_base64(fig) for name, fig in plots.items()}

        # Convert endpoint metrics into DataFrame for easy HTML table rendering
        if type(endpoint_metrics) == pd.DataFrame:
            endpoint_df = endpoint_metrics
        else:
            endpoint_df = pd.DataFrame(endpoint_metrics)

        # Convert global metrics to dictionary if global_metrics is dataframe
        if type(global_metrics) == pd.DataFrame:
            global_metrics = global_metrics.to_dict(orient="records")[0]

        # Render template
        html_content = self.template.render(
            global_metrics=global_metrics,
            endpoint_table=endpoint_df.to_html(classes="table table-striped", index=False),
            plots=plot_images,
        )

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ Report generated at {output_file}")

    def report_pipeline(self, global_metrics: pd.DataFrame, endpoint_metrics: pd.DataFrame, output_file: str):
        """
        Pipeline to generate a report.
        """
        global_metrics = global_metrics.to_dict(orient="records")[0]
        plots = {
            "status_dist": plot_status_distribution(global_metrics),
            "latencies": plot_endpoint_latencies(endpoint_metrics),
            "rps": plot_endpoint_rps(endpoint_metrics)
        }

        self.generate_report(global_metrics, endpoint_metrics, plots, output_file)
