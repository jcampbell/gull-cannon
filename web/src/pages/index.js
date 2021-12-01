import * as React from "react"

import Layout from "../components/layout"
import Seo from "../components/seo"
import FireControl from "../components/fire-control";

const IndexPage = () => (
  <Layout>
    <Seo title="Home" />
    <p>IoT with a bang.</p>
    <FireControl />
  </Layout>
)

export default IndexPage
