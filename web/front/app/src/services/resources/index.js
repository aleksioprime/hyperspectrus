import { UserResource } from "./user.resource";
import { RoleResource } from "./role.resource";
import { AuthResource } from "./auth.resource";
import { OrganizationResource } from "./organization.resource"
import { PatientResource } from "./patient.resource";
import { SessionResource } from "./session.resource";
import { RawImageResource } from "./rawImage.resource";
import { DeviceResource } from "./device.resource";
import { SpectrumResource } from "./spectrum.resource";

export default {
    user: new UserResource(),
    role: new RoleResource(),
    auth: new AuthResource(),
    organization: new OrganizationResource(),
    patient: new PatientResource(),
    session: new SessionResource(),
    rawImage: new RawImageResource(),
    device: new DeviceResource(),
    spectrum: new SpectrumResource(),
};