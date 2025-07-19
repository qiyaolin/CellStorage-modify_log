import pandas as pd
from io import BytesIO
from .. import db
from .models import InventoryItem, Supplier, Location

class DataImportExportService:
    @staticmethod
    def import_inventory_from_file(file, user_id):
        try:
            df = pd.read_excel(file) if file.filename.endswith('.xlsx') else pd.read_csv(file)
            
            required_columns = ['物品名称', '供应商', '当前数量', '单位']
            errors = DataImportExportService.validate_import_data(df, required_columns)
            if errors:
                return {'success': False, 'errors': errors}

            success_count = 0
            for index, row in df.iterrows():
                try:
                    supplier = Supplier.query.filter_by(name=row['供应商']).first()
                    if not supplier:
                        supplier = Supplier(name=row['供应商'])
                        db.session.add(supplier)
                        db.session.flush()

                    location = Location.query.filter_by(full_path=row['存储位置']).first()

                    item = InventoryItem(
                        name=row['物品名称'],
                        catalog_number=row.get('产品编号'),
                        supplier_id=supplier.id,
                        current_quantity=row['当前数量'],
                        unit=row['单位'],
                        minimum_quantity=row.get('最小库存', 0),
                        expiration_date=pd.to_datetime(row.get('到期日期'), errors='coerce'),
                        location_id=location.id if location else None,
                        cas_number=row.get('CAS号'),
                        lot_number=row.get('批次号'),
                        description=row.get('备注'),
                        created_by_user_id=user_id
                    )
                    db.session.add(item)
                    success_count += 1
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            if errors:
                db.session.rollback()
                return {'success': False, 'errors': errors}

            db.session.commit()
            return {'success': True, 'imported_count': success_count}

        except Exception as e:
            return {'success': False, 'errors': [str(e)]}

    @staticmethod
    def validate_import_data(df, required_columns):
        errors = []
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        for index, row in df.iterrows():
            if pd.isna(row.get('物品名称')):
                errors.append(f"Row {index+2}: 物品名称 cannot be empty")
            try:
                float(row.get('当前数量', 0))
            except (ValueError, TypeError):
                errors.append(f"Row {index+2}: 当前数量 must be a number")
        return errors

    @staticmethod
    def export_template():
        template_data = {
            '物品名称*': ['Antibody XYZ'],
            '产品编号': ['AB12345'],
            '供应商*': ['ThermoFisher'],
            '当前数量*': [10],
            '单位*': ['mL'],
            '最小库存': [2],
            '到期日期': ['2024-12-31'],
            '存储位置': ['Room101>Fridge>Shelf1'],
            'CAS号': ['12345-67-8'],
            '批次号': ['LOT001'],
            '备注': ['For experiment']
        }
        df = pd.DataFrame(template_data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Template')
        output.seek(0)
        return output
