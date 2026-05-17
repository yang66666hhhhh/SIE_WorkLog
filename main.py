from utils.optimized_processor import OptimizedWorkRecordProcessor

if __name__ == "__main__":
    processor = OptimizedWorkRecordProcessor()
    processor.process("工作记录.xlsx", "任务级数据.xlsx")
