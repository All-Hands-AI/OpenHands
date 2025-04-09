import { ExpandAltOutlined } from "@ant-design/icons";
import {
  toggleViewDistillComputer,
  useDistillComputerStore,
} from "~/core/store";

const DistillComputerMinimize = () => {
  const isViewDrawer = useDistillComputerStore((state) => state.isViewDrawer);

  if (!isViewDrawer) {
    return (
      <div className="relative mb-2 flex h-10 items-center justify-center rounded-2xl bg-gray-200 text-center">
        <div
          className="group absolute -top-9 left-4 h-[68px] w-[100px] cursor-pointer rounded-lg bg-gray-300 transition-all duration-300 hover:scale-105"
          onClick={() => toggleViewDistillComputer(!isViewDrawer)}
        >
          <div className="flex h-full w-full items-end justify-end p-2">
            <div className="hidden transition-all duration-300 group-hover:block">
              <ExpandAltOutlined />
            </div>
            <div className="absolute -top-7 left-1/2 hidden h-[24px] w-[150px] -translate-x-1/2 items-center justify-center rounded-[6px] bg-gray-800 transition-all duration-300 group-hover:block">
              <span className="text-[12px] text-white transition-all duration-300 group-hover:text-gray-300">
                View Distill's Computer
              </span>
            </div>
          </div>
        </div>
        <span>Finalize</span>
      </div>
    );
  }

  return <div />;
};

export default DistillComputerMinimize;
