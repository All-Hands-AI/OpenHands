// import { FaSlack, FaDiscord, FaGithub } from "react-icons/fa";

// function CustomFooter() {
//   return (
//     <footer style={{ backgroundColor: 'dark' }} className="text-white  h-[25vh] bg-gradient-to-b from-gray-900 to-gray-900">
//         <div className="flex flex-col justify-between w-full items-center p-2 h-full">
//           <div className="flex gap-2">
//             <div className="font-bold  text-lg md:text-3xl">OpenDevin</div>
//             <div className="text-sm"><a className="hover:text-white transition-all duration-300 cursor-pointer hover:no-underline" href="/modules/usage/intro">Docs</a></div>
//           </div>
//             <div className="uppercase font-light">Community</div>
//           <div className="flex gap-6 text-3xl">
//               <div><a className="hover:text-white trasnition-all duration-300" href="https://join.slack.com/t/opendevin/shared_invite/zt-2ggtwn3k5-PvAA2LUmqGHVZ~XzGq~ILw" target="_blank"><FaSlack /></a></div>
//               <div><a className="hover:text-white trasnition-all duration-300" href="https://discord.gg/ESHStjSjD4" target="_blank"><FaDiscord /></a></div>
//               <div><a className="hover:text-white trasnition-all duration-300" href="https://github.com/OpenDevin/OpenDevin" target="_blank"><FaGithub /></a></div>
//           </div>
//           <div >
//           </div>
//         <div >
//           <p className="uppercase">Copyright &copy; {new Date().getFullYear()} OpenDevin</p>
//         </div>
//       </div>
//     </footer>
//   );
// }

// export default CustomFooter;


import React from "react";
import { FaSlack, FaDiscord, FaGithub } from "react-icons/fa";
import "../css/footer.css"; // Importing the CSS file

function CustomFooter() {
  return (
    <footer className="custom-footer">
      <div className="footer-content">
        <div className="footer-top">
          <div className="footer-title">OpenDevin</div>
          <div className="footer-link">
            <a href="/modules/usage/intro">Docs</a>
          </div>
        </div>
        <div className="footer-community">Community</div>
        <div className="footer-icons">
          <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2ggtwn3k5-PvAA2LUmqGHVZ~XzGq~ILw" target="_blank" rel="noopener noreferrer">
            <FaSlack />
          </a>
          <a href="https://discord.gg/ESHStjSjD4" target="_blank" rel="noopener noreferrer">
            <FaDiscord />
          </a>
          <a href="https://github.com/OpenDevin/OpenDevin" target="_blank" rel="noopener noreferrer">
            <FaGithub />
          </a>
        </div>
        <div className="footer-bottom">
          <p>Copyright &copy; {new Date().getFullYear()} OpenDevin</p>
        </div>
      </div>
    </footer>
  );
}

export default CustomFooter;
