"""
Demo Service - Creates sample project and runs complete DIA workflow
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from decimal import Decimal

from models.base import Project, DrainageArea, Run, Result
from services.module_c.rational_method import RationalMethodCalculator, TimeOfConcentration
from services.module_b.noaa_parser import NOAAAtlas14Parser


class DemoService:
    """
    Demo service that showcases the complete DIA workflow

    This service:
    1. Creates a demo project with realistic data
    2. Creates sample drainage areas
    3. Runs the complete DIA report generation
    """

    def __init__(self, db: Session):
        self.db = db
        self.rational_calc = RationalMethodCalculator()
        self.noaa_parser = NOAAAtlas14Parser()

    def create_demo_project(self) -> Dict[str, Any]:
        """
        Create a demo project with sample drainage areas

        Returns:
            Dict containing project_id and drainage_area_ids
        """
        # Create demo project
        project = Project(
            id=uuid.uuid4(),
            name="Acadian Village Parking Expansion - DEMO",
            project_number=f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            client_name="Acadian Village Association",
            location="Lafayette, LA",
            project_type="Commercial Development",
            jurisdiction="Lafayette UDC",
            status="active",
            extra_data={
                "description": "Parking lot expansion with drainage improvements - DEMONSTRATION",
                "is_demo": True,
                "created_for": "demonstration_purposes"
            }
        )

        self.db.add(project)
        self.db.flush()

        # Create sample drainage areas based on the demo guide test data
        drainage_areas_data = [
            {
                "area_label": "E-DA1",
                "total_area_sqft": Decimal("25000"),
                "total_area_acres": Decimal("0.574"),
                "impervious_area_sqft": Decimal("20000"),
                "impervious_area_acres": Decimal("0.459"),
                "pervious_area_sqft": Decimal("5000"),
                "pervious_area_acres": Decimal("0.115"),
                "weighted_c_value": Decimal("0.744"),
                "land_use_breakdown": {
                    "Pavement": {"area_sqft": 15000, "c_value": 0.90, "percentage": 60.0},
                    "Grass - Flat": {"area_sqft": 5000, "c_value": 0.15, "percentage": 20.0},
                    "Concrete Sidewalk": {"area_sqft": 2000, "c_value": 0.85, "percentage": 8.0},
                    "Gravel": {"area_sqft": 3000, "c_value": 0.20, "percentage": 12.0}
                },
                "notes": "Mixed-use parking lot - main drainage area"
            },
            {
                "area_label": "E-DA2",
                "total_area_sqft": Decimal("18000"),
                "total_area_acres": Decimal("0.413"),
                "impervious_area_sqft": Decimal("12000"),
                "impervious_area_acres": Decimal("0.275"),
                "pervious_area_sqft": Decimal("6000"),
                "pervious_area_acres": Decimal("0.138"),
                "weighted_c_value": Decimal("0.625"),
                "land_use_breakdown": {
                    "Pavement": {"area_sqft": 10000, "c_value": 0.90, "percentage": 55.6},
                    "Grass - Average": {"area_sqft": 6000, "c_value": 0.25, "percentage": 33.3},
                    "Gravel": {"area_sqft": 2000, "c_value": 0.20, "percentage": 11.1}
                },
                "notes": "Secondary parking area"
            },
            {
                "area_label": "E-DA3",
                "total_area_sqft": Decimal("12500"),
                "total_area_acres": Decimal("0.287"),
                "impervious_area_sqft": Decimal("8500"),
                "impervious_area_acres": Decimal("0.195"),
                "pervious_area_sqft": Decimal("4000"),
                "pervious_area_acres": Decimal("0.092"),
                "weighted_c_value": Decimal("0.680"),
                "land_use_breakdown": {
                    "Roof": {"area_sqft": 5000, "c_value": 0.85, "percentage": 40.0},
                    "Pavement": {"area_sqft": 3500, "c_value": 0.90, "percentage": 28.0},
                    "Grass - Flat": {"area_sqft": 4000, "c_value": 0.15, "percentage": 32.0}
                },
                "notes": "Building and entrance area"
            }
        ]

        drainage_area_ids = []
        for da_data in drainage_areas_data:
            drainage_area = DrainageArea(
                id=uuid.uuid4(),
                project_id=project.id,
                drawing_id=None,  # No drawing for demo
                **da_data
            )
            self.db.add(drainage_area)
            drainage_area_ids.append(str(drainage_area.id))

        self.db.commit()

        return {
            "project_id": str(project.id),
            "project_number": project.project_number,
            "project_name": project.name,
            "drainage_areas": len(drainage_areas_data),
            "drainage_area_ids": drainage_area_ids,
            "total_area_acres": float(sum(da["total_area_acres"] for da in drainage_areas_data)),
            "message": "Demo project created successfully!"
        }

    def run_dia_demo(
        self,
        project_id: str,
        storm_events: List[str] = None,
        tc_method: str = "nrcs"
    ) -> Dict[str, Any]:
        """
        Run complete DIA workflow for demo project

        Args:
            project_id: UUID of the demo project
            storm_events: List of storm events (default: ["10-year", "25-year"])
            tc_method: Tc calculation method (default: "nrcs")

        Returns:
            Dict containing run results and file paths
        """
        if storm_events is None:
            storm_events = ["10-year", "25-year"]

        # Get project
        project = self.db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get drainage areas
        drainage_areas = self.db.query(DrainageArea).filter(
            DrainageArea.project_id == uuid.UUID(project_id)
        ).all()

        if not drainage_areas:
            raise ValueError(f"No drainage areas found for project {project_id}")

        # Create run
        run = Run(
            id=uuid.uuid4(),
            project_id=project.id,
            run_type="dia_report",
            storm_events=storm_events,
            parameters={
                "tc_method": tc_method,
                "include_exhibits": True,
                "include_noaa_appendix": True,
                "is_demo": True
            },
            status="processing",
            created_by="demo_service"
        )

        self.db.add(run)
        self.db.flush()

        # Process each storm event
        all_results = []
        results_by_storm = {}

        try:
            for storm_event in storm_events:
                # Extract return period (e.g., "10-year" -> 10)
                return_period = int(storm_event.replace("-year", ""))
                storm_results = []

                for drainage_area in drainage_areas:
                    # Calculate Time of Concentration
                    # For demo, use realistic flow length and elevation change
                    flow_length_ft = 850.0  # feet
                    elevation_change_ft = 8.5  # feet

                    if tc_method.lower() == "nrcs":
                        tc_minutes = TimeOfConcentration.nrcs_method(
                            flow_length_ft=flow_length_ft,
                            elevation_change_ft=elevation_change_ft,
                            cn=75  # Typical urban residential
                        )
                    elif tc_method.lower() == "kirpich":
                        tc_minutes = TimeOfConcentration.kirpich_method(
                            flow_length_ft=flow_length_ft,
                            elevation_change_ft=elevation_change_ft
                        )
                    elif tc_method.lower() == "faa":
                        tc_minutes = TimeOfConcentration.faa_method(
                            flow_length_ft=flow_length_ft,
                            runoff_coefficient=float(drainage_area.weighted_c_value),
                            slope_percent=1.0
                        )
                    else:
                        tc_minutes = 12.5  # Default

                    # Get rainfall intensity from NOAA
                    intensity = self.noaa_parser.get_intensity(
                        duration_minutes=tc_minutes,
                        return_period_years=return_period
                    )

                    if intensity is None:
                        # Interpolate if needed
                        intensity = self.noaa_parser.interpolate_intensity(
                            duration_minutes=tc_minutes,
                            return_period_years=return_period
                        )

                    if intensity is None:
                        # Use typical values for Lafayette, LA
                        intensity_map = {
                            10: 7.25,  # 10-year
                            25: 8.50,  # 25-year
                            50: 9.50,  # 50-year
                            100: 10.50  # 100-year
                        }
                        intensity = intensity_map.get(return_period, 7.25)

                    # Calculate peak flow using Rational Method: Q = CiA
                    c_value = float(drainage_area.weighted_c_value)
                    area_acres = float(drainage_area.total_area_acres)
                    peak_flow_cfs = c_value * intensity * area_acres

                    # Create result record
                    result = Result(
                        id=uuid.uuid4(),
                        run_id=run.id,
                        drainage_area_id=drainage_area.id,
                        storm_event=storm_event,
                        c_value=Decimal(str(c_value)),
                        i_value=Decimal(str(intensity)),
                        area_acres=drainage_area.total_area_acres,
                        peak_flow_cfs=Decimal(str(round(peak_flow_cfs, 2))),
                        tc_minutes=Decimal(str(round(tc_minutes, 2))),
                        tc_method=tc_method,
                        development_condition="post",
                        calculation_details={
                            "flow_length_ft": flow_length_ft,
                            "elevation_change_ft": elevation_change_ft,
                            "is_demo": True
                        }
                    )

                    self.db.add(result)
                    storm_results.append({
                        "drainage_area_label": drainage_area.area_label,
                        "c_value": c_value,
                        "i_value": intensity,
                        "area_acres": area_acres,
                        "tc_minutes": round(tc_minutes, 2),
                        "peak_flow_cfs": round(peak_flow_cfs, 2)
                    })
                    all_results.append(result)

                results_by_storm[storm_event] = storm_results

            # Update run status
            run.status = "completed"
            run.completed_at = datetime.now()
            run.results_summary = {
                "total_drainage_areas": len(drainage_areas),
                "storm_events_analyzed": storm_events,
                "results_by_storm": results_by_storm,
                "project_info": {
                    "name": project.name,
                    "number": project.project_number,
                    "client": project.client_name,
                    "location": project.location
                },
                "report_paths": {
                    "main_report": f"/app/outputs/DIA_Report_{project.project_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    "exhibits": [
                        f"/app/outputs/Exhibit_3A_{storm_events[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                        f"/app/outputs/Exhibit_3B_{storm_events[1] if len(storm_events) > 1 else storm_events[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    ]
                },
                "is_demo": True,
                "demo_note": "This is a demonstration run with sample data"
            }

            self.db.commit()

            return {
                "run_id": str(run.id),
                "project_id": str(project.id),
                "status": "completed",
                "results_summary": run.results_summary,
                "total_results": len(all_results),
                "message": "DIA demo completed successfully!"
            }

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            self.db.commit()
            raise

    def get_demo_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get status of a demo run

        Args:
            run_id: UUID of the run

        Returns:
            Dict containing run status and results
        """
        run = self.db.query(Run).filter(Run.id == uuid.UUID(run_id)).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        # Get results
        results = self.db.query(Result).filter(Result.run_id == run.id).all()

        return {
            "run_id": str(run.id),
            "project_id": str(run.project_id),
            "status": run.status,
            "run_type": run.run_type,
            "storm_events": run.storm_events,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "results_count": len(results),
            "results_summary": run.results_summary,
            "error_message": run.error_message
        }
