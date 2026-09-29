import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

const LINK_REGEX = new RegExp("^https?://");
const ODOO_COM_REGEX = /^https?:\/\/([a-z0-9-]+\.)*odoo\.com(\/|$)/i;

export class DocumentationLink extends Component {
    static template = "web.DocumentationLink";
    static props = {
        ...standardWidgetProps,
        record: { type: Object, optional: 1 }, // The record is not needed in this widget
        path: { type: String },
        label: { type: String, optional: 1 },
        icon: { type: String, optional: 1 },
        alertLink: { type: Boolean, optional: 1 },
    };

    // ДАО КООПТЕХ: ссылки на документацию вели на сайт Odoo S.A. Показываем
    // только свои абсолютные адреса; относительные пути и odoo.com — без ссылки.
    get url() {
        const path = this.props.path || "";
        if (LINK_REGEX.test(path) && !ODOO_COM_REGEX.test(path)) {
            return path;
        }
        return "";
    }

    get classes() {
        let classes = "o_doc_link me-2";
        if (this.props.alertLink){
            classes += " alert-link";
        }
        return classes;
    }
}

export const documentationLink = {
    component: DocumentationLink,
    extractProps: ({ attrs }) => {
        const { path, label, icon, alert_link } = attrs;
        return {
            path,
            label,
            icon,
            alertLink: Boolean(alert_link),
        };
    },
    additionalClasses: ["d-inline"],
};

registry.category("view_widgets").add("documentation_link", documentationLink);
