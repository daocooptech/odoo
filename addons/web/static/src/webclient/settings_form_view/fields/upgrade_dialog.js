import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

import { Component, t, useProps } from "@odoo/owl";

export class UpgradeDialog extends Component {
    static template = "web.UpgradeDialog";
    static components = { Dialog };
    props = useProps({
        close: t.function(),
    });
    setup() {
        this.orm = useService("orm");
    }
    // ДАО КООПТЕХ: переход на страницу покупки Odoo Enterprise убран.
    async _confirmUpgrade() {
        this.props.close();
    }
}
