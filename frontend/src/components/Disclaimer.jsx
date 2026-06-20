/**
 * Disclaimer component.
 *
 * The application must always make clear that analytical signals are not
 * investment advice.
 */

function Disclaimer({ text }) {
  if (!text) {
    return null;
  }

  return <div className="disclaimer-box">{text}</div>;
}

export default Disclaimer;