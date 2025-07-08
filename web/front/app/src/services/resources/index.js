import { UserResource } from "./user.resource";
import { RoleResource } from "./role.resource";
import { AuthResource } from "./auth.resource";
import { OrganizationResource } from "./organization.resource"
import { ChromophoreResource } from "./chromophore.resource";
import { DeviceResource } from "./device.resource";
import { SpectrumResource } from "./spectrum.resource";
import { OverlapMatrixResource } from "./overlapMatrix.resources"
import { PatientResource } from "./patient.resource";
import { SessionResource } from "./session.resource";
import { RawImageResource } from "./rawImage.resource";

export default {
    user: new UserResource(),
    role: new RoleResource(),
    auth: new AuthResource(),
    organization: new OrganizationResource(),
    chromophore: new ChromophoreResource(),
    device: new DeviceResource(),
    spectrum: new SpectrumResource(),
    overlapMatrix: new OverlapMatrixResource(),
    patient: new PatientResource(),
    session: new SessionResource(),
    rawImage: new RawImageResource(),
};