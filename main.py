from utils.processor import WorkRecordProcessor

if __name__ == "__main__":
    processor = WorkRecordProcessor()
    processor.process("工作记录.xlsx", "任务级数据.xlsx")
